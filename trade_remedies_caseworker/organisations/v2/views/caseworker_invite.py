from abc import ABC, abstractmethod

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import FormView
from v2_api_client.mixins import APIClientMixin

from config.forms import ValidationForm
from organisations.forms import (
    OrganisationInviteContactForm,
    OrganisationInviteContactNewForm,
    OrganisationInviteForm,
)


class BaseOrganisationInviteView(LoginRequiredMixin, FormView, APIClientMixin, ABC):
    def dispatch(self, *args, **kwargs):
        if "organisation_invitation" not in self.request.session:
            self.request.session["organisation_invitation"] = {}
        self.request.session.modified = True
        return super().dispatch(*args, **kwargs)

    def reset_session(self, request, initial_data=None):
        initial_data = initial_data or {}
        request.session["organisation_invitation"] = initial_data
        request.session.modified = True
        return request.session

    def update_session(self, request, update_data):
        request.session.setdefault("organisation_invitation", {})
        if isinstance(update_data, QueryDict):
            # If it's a QueryDict, we need to convert it to a normal dictionary as Django's
            # internal representation of QueryDicts store individual values as lists, regardless
            # of how many elements are in that list
            # https://www.ianlewis.org/en/querydict-and-update
            update_data = update_data.dict()
        request.session["organisation_invitation"].update(update_data)
        request.session.modified = True
        return request.session

    def form_invalid(self, form):
        form.assign_errors_to_request(self.request)
        return super().form_invalid(form)

    def form_valid(self, form):
        self.update_session(self.request, form.cleaned_data)
        return redirect(self.get_next_url(form))

    @abstractmethod
    def get_next_url(self, form=None):
        # This method must be implemented in the subclass
        pass


class OrganisationInviteView(BaseOrganisationInviteView):
    template_name = "organisations/organisation_invitation.html"
    form_class = OrganisationInviteForm

    def dispatch(self, *args, **kwargs):
        self.request.session["case_role_key"] = self.request.GET["case_role_key"]
        return super().dispatch(*args, **kwargs)

    # for use in html template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["case_id"] = self.kwargs["case_id"]
        return context

    def get_next_url(self, form=None):
        # Existing organisation (and contact(s))
        self.request.session["new_contact"] = False
        return reverse(
            "organisations:invite-party-contacts-choice",
            kwargs={
                "case_id": self.kwargs["case_id"],
                "organisation_id": form.cleaned_data.get("organisation_id"),
            },
        )


class OrganisationInviteContactsView(BaseOrganisationInviteView):
    template_name = "organisations/invite_party_contacts_choice.html"
    form_class = OrganisationInviteContactForm

    def dispatch(self, *args, **kwargs):
        # now let's get the list of contacts associated with the org
        # list of tuples containing (owner or employee) contacts for the organisation
        org_contacts = self.client.organisations(
            self.kwargs["organisation_id"], fields=["contacts"]
        ).contacts
        # extract org-related (owner or employees) users from contact list
        org_users = [contact for contact in org_contacts if contact.has_user]

        # get contacts who have represented the organisation (but are not owner or employees)
        rep_contacts = self.client.organisations(
            self.kwargs["organisation_id"], fields=["representative_contacts"]
        ).representative_contacts
        # extract rep users from contact list. This step might not be required?
        rep_users = [contact for contact in rep_contacts if contact.has_user]

        # combine the two lists of users
        all_users = org_users + rep_users

        # Extract id, name, and email into tuples. These tuples will be in a list.
        # Choices in form is expecting only two fields per tuple, therefore merge
        # name and email
        contacts_list = [(each.id, f"{each.name} - {each.email}") for each in all_users]

        # remove duplicates
        contacts_list = list(set(contacts_list))

        # Sort the tuples in alphabetical (name + email are index 1)
        # order
        contacts_list.sort(key=lambda x: x[1])
        self.contacts_list = contacts_list

        return super().dispatch(*args, **kwargs)

    # for use in html template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)
        context["org_invite_contacts"] = self.contacts_list
        return context

    # for use in form
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["org_invite_contacts"] = self.contacts_list
        return kwargs

    def form_valid(self, form):
        # selected contacts
        self.request.session["selected_contacts"] = self.request.POST.getlist("which_contact")
        return super().form_valid(form)

    def get_next_url(self, form=None):
        return reverse(
            "organisations:invite-party-check",
            kwargs={
                "case_id": self.kwargs["case_id"],
                "organisation_id": self.kwargs["organisation_id"],
            },
        )


class OrganisationInviteContactNewView(BaseOrganisationInviteView):
    template_name = "organisations/invite_party_contact_new.html"
    form_class = OrganisationInviteContactNewForm

    # for use in html template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)

        # self.request.session["new_contact"] might not be set yet
        if self.request.session.get("new_contact") and "selected_contacts" in self.request.session:
            contact = self.client.contacts(self.request.session["selected_contacts"][0])
            context["selected_contact_name"] = contact.name
            context["selected_contact_email"] = contact.email
            context["selected_organisation"] = self.client.organisations(
                contact.organisation, fields=["name"]
            ).name

        return context

    def form_valid(self, form):
        # Create new organisation
        organisation = self.client.organisations(
            {"name": form.cleaned_data["organisation_name"]}, fields=["id"]
        )
        self.kwargs["organisation_id"] = organisation.id

        # Create new contact and associate with (new) organisation
        contact = self.client.contacts(
            {
                "name": form.cleaned_data["contact_name"],
                "email": form.cleaned_data["contact_email"],
                "organisation": organisation.id,
            }
        )
        self.request.session["selected_contacts"] = [
            contact["id"],
        ]
        self.request.session["new_contact"] = True
        return super().form_valid(form)

    def get_next_url(self, form=None):
        return reverse(
            "organisations:invite-party-check",
            kwargs={
                "case_id": self.kwargs["case_id"],
                "organisation_id": self.kwargs["organisation_id"],
            },
        )


class OrganisationInviteReviewView(BaseOrganisationInviteView):
    template_name = "organisations/invite_party_check.html"
    form_class = ValidationForm

    def dispatch(self, *args, **kwargs):
        selected_contacts = []
        for contact_id in self.request.session.get("selected_contacts", []):
            contact = self.client.contacts(contact_id, fields=["name", "email"])
            selected_contacts.append(contact)
        self.selected_contacts = selected_contacts
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)

        context["case_id"] = self.kwargs["case_id"]
        context["organisation_id"] = self.kwargs["organisation_id"]
        context["case"] = self.client.cases(self.kwargs["case_id"], fields=["name", "reference"])
        context["organisation"] = self.client.organisations(
            self.kwargs["organisation_id"], fields=["name"]
        )

        context["selected_contacts"] = self.selected_contacts
        context["new_contact"] = self.request.session.get("new_contact", False)

        return context

    def get_next_url(self, form=None):
        return reverse(
            "organisations:invite-party-complete",
            kwargs={
                "case_id": self.kwargs["case_id"],
            },
        )

    def post(self, request, *args, **kwargs):
        # create and invitation for each contact and send
        for contact in self.selected_contacts:
            new_invitation = self.client.invitations(
                {
                    "organisation": self.kwargs["organisation_id"],
                    "case": self.kwargs["case_id"],
                    "contact": contact.id,
                    "invitation_type": 3,
                    "name": contact.name,
                    "email": contact.email,
                    "case_role_key": self.request.session["case_role_key"],
                }
            )
            new_invitation.send()
        return redirect(self.get_next_url())


class OrganisationInviteCompleteView(BaseOrganisationInviteView):
    template_name = "organisations/invite_party_complete.html"
    form_class = ValidationForm

    def clean_session_data(self):
        # clean up session data
        self.request.session.pop("new_contact", None)
        self.request.session.pop("selected_contacts", None)
        self.request.session.pop("case_role_key", None)

    def get_selected_contacts(self):
        selected_contacts = []
        for contact_id in self.request.session.get("selected_contacts", []):
            contact = self.client.contacts(contact_id, fields=["name", "email"])
            selected_contacts.append(contact)
        return selected_contacts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["case_id"] = self.kwargs["case_id"]
        context["selected_contacts"] = self.get_selected_contacts()
        context["case_role_key"] = self.request.session["case_role_key"]
        self.clean_session_data()
        return context

    def get_next_url(self, form=None):
        return f'/case/{self.kwargs["case_id"]}/'
