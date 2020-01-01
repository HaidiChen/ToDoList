from django.test import TestCase
from lists.forms import EMPTY_ITEM_ERROR, ItemForm

class ItemFormTest(TestCase):

    def test_form_validation_for_blank_items(self):
        form = ItemForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['text'], [EMPTY_ITEM_ERROR])
