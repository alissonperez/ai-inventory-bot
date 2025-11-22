import pytest
from inventorybot.entities import Item, Status, Location

def test_item_validation_success():
    location = Location(name="Box 1")
    item = Item(name="Test Item", quantity=1, location=location)
    item.validate()  # Should not raise

def test_item_validation_missing_name():
    location = Location(name="Box 1")
    item = Item(quantity=1, location=location)
    with pytest.raises(ValueError, match="Nome é obrigatório"):
        item.validate()

def test_item_validation_missing_quantity():
    location = Location(name="Box 1")
    item = Item(name="Test Item", location=location)
    with pytest.raises(ValueError, match="Quantidade é obrigatória"):
        item.validate()

def test_item_validation_missing_location():
    item = Item(name="Test Item", quantity=1)
    with pytest.raises(ValueError, match="Localização é obrigatória"):
        item.validate()

def test_item_to_dict():
    location = Location(name="Box 1")
    item = Item(
        name="Test Item",
        description="A test item",
        quantity=5,
        size="M",
        status=Status.DISPONIVEL,
        photo="path/to/photo.jpg",
        tags=["tag1", "tag2"],
        location=location
    )
    
    expected_dict = {
        "name": "Test Item",
        "description": "A test item",
        "quantity": 5,
        "size": "M",
        "status": "disponivel",
        "photo": "path/to/photo.jpg",
        "tags": ["tag1", "tag2"],
        "borrowed_by": None,
        "borrowed_date": None,
        "location": {
            "name": "Box 1",
            "filename": "box-1 - Inventário",
            "location": ""
        }
    }
    
    assert item.to_dict() == expected_dict

def test_item_filename():
    item = Item(name="Test Item")
    filename = item.filename()
    assert filename.startswith("test-item-")
    assert len(filename) == len("test-item-") + Item.NUM_RANDOM_CHARS_FILENAME

def test_item_cover_filename():
    item = Item(name="Test Item", photo="/path/to/photo.jpg")
    assert item.cover_filename() == "photo.jpg"

def test_item_cover_filename_none():
    item = Item(name="Test Item")
    assert item.cover_filename() is None
