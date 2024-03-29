from unittest import TestCase

from organisations.forms import (
    OrganisationInviteForm,
    OrganisationInviteContactForm,
    OrganisationInviteContactNewForm,
)


class TestOrganisationInviteForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "organisation_name": "TEST COMPANY",
            "organisation_address": "1 TEST ROAD, LONDON, UNITED KINGDOM, NNN NNN",
            "organisation_post_code": "NNN NNN",  # /PS-IGNORE
            "companies_house_id": "000000",
            "organisation_id": "aor4nd0m-idoo-foro-test-purp05e5oooo",
        }

    def test_valid_form(self):
        self.mock_data["input-autocomplete"] = "TEST"
        form = OrganisationInviteForm(data=self.mock_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            {
                "organisation_id": "aor4nd0m-idoo-foro-test-purp05e5oooo",
            },
            form.cleaned_data,
        )

    def test_organisations_searched_but_not_selected(self):
        form = OrganisationInviteForm(data={"input-autocomplete": "TEST"})
        self.assertFalse(form.is_valid())
        assert "organisation_not_selected" in form.errors["organisation_id"]

    def test_organisations_not_searched(self):
        form = OrganisationInviteForm(data={"input-autocomplete": ""})
        self.assertFalse(form.is_valid())
        assert "organisation_not_searched" in form.errors["organisation_id"]


class TestOrganisationInviteContactForm(TestCase):
    def setUp(self) -> None:
        # "org_invite_contacts" is data passed into the class - to build checkbox choices
        # "data" is data that is the response from the form (i.e., the selected checkbox(es))

        self.mock_data = {
            "org_invite_contacts": [
                (
                    "aor4nd0m-idoo-foro-test-purp05e5oooo",
                    "Test Name1 - test1@example.com",  # /PS-IGNORE
                ),
                (
                    "an0thero-idoo-t0oo-test-w1thoooooooo",
                    "Test Name2 - test2@example.com",  # /PS-IGNORE
                ),
                (
                    "ando0n3o-m0re-t0oo-test-t1hisoc0d3oo",  # /PS-IGNORE
                    "Test Name3 - test3@example.com",  # /PS-IGNORE
                ),
            ],
            "data": {
                "which_contact": "aor4nd0m-idoo-foro-test-purp05e5oooo"
            },  # selected contact(s)
        }

    def test_valid_org_type_selected(self):
        form = OrganisationInviteContactForm(**self.mock_data)
        self.assertTrue(form.is_valid())

    def test_no_org_type_selected(self):
        form = OrganisationInviteContactForm(
            org_invite_contacts=[
                (
                    "aor4nd0m-idoo-foro-test-purp05e5oooo",
                    "Test Name1 - test1@example.com",  # /PS-IGNORE
                )
            ],
            data={"which_contact": ""},  # no contact selected
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"which_contact": [{"message": "no_contact_selected", ' '"code": "required"}]}',
        )


class TestOrganisationInviteContactNewForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "organisation_name": "test organisation",
            "contact_name": "test",
            "contact_email": "test@example.com",  # /PS-IGNORE
        }

    def test_valid_input(self):
        form = OrganisationInviteContactNewForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_no_organisation_name(self):
        self.mock_data.update(
            {
                "organisation_name": "",
                "contact_name": "test",
                "contact_email": "test@example.com",  # /PS-IGNORE
            }
        )
        form = OrganisationInviteContactNewForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"organisation_name": '
            '[{"message": "invite_contact_no_organisation_name", "code": "required"}]}',
        )

    def test_no_contact_name(self):
        self.mock_data.update(
            {
                "organisation_name": "test organisation",
                "contact_name": "",
                "contact_email": "test@example.com",  # /PS-IGNORE
            }
        )
        form = OrganisationInviteContactNewForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"contact_name": [{"message": "invite_contact_no_name", "code": "required"}]}',
        )

    def test_no_contact_email(self):
        self.mock_data.update(
            {
                "organisation_name": "test organisation",
                "contact_name": "test",
                "contact_email": "",
            }
        )
        form = OrganisationInviteContactNewForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"contact_email": [{"message": "invite_contact_no_email", "code": "required"}]}',
        )

    def test_invalid_email(self):
        self.mock_data.update(
            {
                "organisation_name": "test organisation",
                "contact_name": "test",
                "contact_email": "test.com",
            }
        )
        form = OrganisationInviteContactNewForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"contact_email": [{"message": "invite_contact_invalid_email", "code": "invalid"}]}',
        )
