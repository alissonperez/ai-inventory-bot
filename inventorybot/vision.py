from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI
from icecream import ic


@dataclass
class VisionResult:
    name: str
    description: str
    brand: str | None = None
    color: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VisionResult":
        return cls(
            name=str(data.get("name", "N/A")),
            description=str(data.get("description", "")),
            brand=(None if data.get("brand") in ("", None) else str(data.get("brand"))),
            color=(None if data.get("color") in ("", None) else str(data.get("color"))),
        )


class VisionService:
    """
    Serviço para extrair detalhes de um item a partir de uma imagem,
    usando a OpenAI Responses API (visão multimodal) com capacidade de busca web.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enable_search: bool = True,
    ):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY ausente.")
        self.client = OpenAI(api_key=api_key)

        # Modelo padrão com visão; ajuste se usar outro deployment.
        # Ex.: "gpt-4o-mini" é visão-capaz e estável.
        self.model = model or os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
        self.enable_search = enable_search

    @staticmethod
    def _encode_image_to_data_url(image_path: str) -> str:
        """
        Lê o arquivo e devolve uma data URL base64 (ex.: data:image/png;base64,....)
        """
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }.get(path.suffix.lower(), "image/jpeg")

        b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """
        Tenta extrair um objeto JSON de uma string que pode conter:
        - cercas de código ```json ... ```
        - texto extra antes/depois
        - múltiplos blocos

        Estratégia:
        1) se começar com ```json, recorta a cerca
        2) regex para pegar o primeiro {...} balanceado (heurístico)
        3) fallback: tenta json.loads direto
        """
        if not text:
            raise ValueError("Resposta vazia.")

        # 1) cerca de código
        fenced = re.search(
            r"```json\s*(.+?)\s*```", text, flags=re.DOTALL | re.IGNORECASE
        )
        if fenced:
            return json.loads(fenced.group(1))

        # 2) heurística: primeiro bloco que pareça JSON-obj
        #    pega do primeiro '{' até o último '}' e tenta fazer loads em janelas decrescentes
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            snippet = text[first : last + 1]
            # tenta direto
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                # tenta "limpar" quebras de linha e vírgulas sobrando
                cleaned = re.sub(r",\s*([}\]])", r"\1", snippet)
                return json.loads(cleaned)

        # 3) última tentativa: json.loads de tudo
        return json.loads(text)

    def extract_item_details_from_image(self, item: Item) -> VisionResult:
        data_url = self._encode_image_to_data_url(item.photo)

        product_info = []
        if item.name:
            product_info.append(f"Nome preenchido pelo usuário: '{item.name}'")
        if item.description:
            product_info.append(
                f"Descrição preenchida pelo usuário: '{item.description}'"
            )

        product_info_str = ""
        if len(product_info) > 0:
            product_info_str = (
                "\n\n## INFORMAÇÕES FORNECIDAS PELO USUÁRIO:\n"
                + "\n".join(product_info)
                + "\n\nIMPORTANTE: Estas são informações parciais do usuário. "
                "Use-as como ponto de partida, mas você DEVE:\n"
                "1. Verificar se correspondem ao que você vê na imagem\n"
                "2. Complementar com detalhes visuais da imagem\n"
                "3. Se o usuário forneceu apenas um nome genérico ou marca, USE A BUSCA WEB para "
                "obter especificações técnicas, modelo exato, ano de fabricação, e outros detalhes relevantes\n"
                "4. Se a imagem mostra embalagem com código de barras, modelo, ou informações específicas, "
                "USE A BUSCA WEB para confirmar e enriquecer os dados\n"
            )

        # Instrução aprimorada para uso de busca web
        search_guidance = ""
        if self.enable_search:
            search_guidance = (
                "\n\n## QUANDO E COMO USAR A BUSCA WEB:\n"
                "Você TEM ACESSO à ferramenta de busca web. Use-a estrategicamente quando:\n\n"
                "1. **Produtos com marca visível**: Busque por 'marca + modelo' para obter especificações exatas\n"
                "2. **Informações do usuário são genéricas**: Ex: usuário disse 'tênis Nike', "
                "busque para identificar o modelo específico (Air Max, Air Force, etc.)\n"
                "3. **Produtos eletrônicos/técnicos**: Sempre busque para obter especificações técnicas completas\n"
                "4. **Embalagens com código/modelo**: Use o código visível na imagem para buscar detalhes\n"
                "5. **Produtos importados/com texto estrangeiro**: Busque para traduzir e obter contexto\n\n"
                "COMO BUSCAR:\n"
                "- Combine marca + modelo visível na imagem ou fornecido pelo usuário\n"
                "- Adicione termos como 'especificações', 'características', 'ficha técnica'\n"
                "- Para produtos em português: busque em PT-BR primeiro\n"
                "- Exemplos de buscas:\n"
                "  * 'Nike Air Max 90 especificações'\n"
                "  * 'Samsung Galaxy S23 ficha técnica'\n"
                "  * 'Lego Star Wars 75192 detalhes'\n\n"
                "NÃO BUSQUE quando:\n"
                "- O produto é genérico sem marca (ex: 'copo plástico vermelho')\n"
                "- A imagem já mostra todos os detalhes necessários claramente\n"
                "- Itens artesanais ou únicos sem referência comercial\n"
            )

        # Prompt completo e estruturado
        prompt = (
            "Você é um assistente especializado em catalogação de inventário. "
            "Sua tarefa é analisar a imagem do produto e retornar informações COMPLETAS e PRECISAS.\n"
            f"{search_guidance}"
            f"{product_info_str}\n"
            "## FORMATO DE SAÍDA:\n"
            "Retorne APENAS um objeto JSON com os campos:\n"
            "- 'name': Nome COMPLETO e ESPECÍFICO do produto (inclua marca, modelo, versão se identificável)\n"
            "- 'description': Descrição DETALHADA incluindo:\n"
            "  * Características visuais da imagem\n"
            "  * Especificações técnicas (se encontradas via busca)\n"
            "  * Material, dimensões aproximadas, estado de conservação\n"
            "  * Qualquer detalhe relevante para inventário\n"
            "- 'brand': Marca/fabricante (se identificável), ou null\n"
            "- 'color': Cor(es) predominante(s), ou null\n\n"
            "IMPORTANTE:\n"
            "- Texto SEMPRE em português do Brasil\n"
            "- Seja ESPECÍFICO, não genérico (ex: 'Tênis Nike Air Max 90 Branco' e não apenas 'Tênis branco')\n"
            "- Use busca web quando apropriado para enriquecer os dados\n"
            "- Combine informações visuais + informações do usuário + dados da web\n"
            "- Retorne APENAS o JSON, sem markdown, sem explicações adicionais\n\n"
            "Exemplo de saída:\n"
            '{"name": "Tênis Nike Air Max 90 Essential", '
            '"description": "Tênis esportivo Nike Air Max 90 na cor branca com detalhes em cinza. '
            "Tecnologia Air visível no calcanhar. Solado em borracha com tração multidirecional. "
            'Cabedal em couro sintético e mesh para respirabilidade. Estado: usado, bom estado de conservação.", '
            '"brand": "Nike", "color": "branco"}\n\n'
            "Agora analise a imagem e retorne o JSON:"
        )

        # Configurar tools para busca web se habilitado
        tools = None
        if self.enable_search:
            tools = [{"type": "web_search"}]

        # Chamada na Responses API com conteúdo multimodal e busca web
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
            tools=tools,
            # max_output_tokens=500,  # Aumentado para acomodar descrições mais detalhadas
        )

        message_text: str = getattr(response, "output_text", "") or ""
        ic(message_text)

        try:
            data = self._extract_json(message_text)
            return VisionResult.from_dict(data)
        except Exception as e:
            raise RuntimeError(
                f"Falha ao interpretar JSON da resposta de visão: {e}"
            ) from e
