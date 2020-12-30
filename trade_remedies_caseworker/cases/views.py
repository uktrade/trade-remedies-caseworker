import json
import logging
import re
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from core.base import GroupRequiredMixin
from core.utils import (
    deep_index_items_by,
    deep_index_items_by_exists,
    get,
    key_by,
    index_users_by_group,
    compact_list,
    submission_contact,
    public_login_url,
    parse_notify_template,
    parse_api_datetime,
    pluck,
    to_json,
    from_json,
    deep_update,
)
from django_countries import countries
from django.conf import settings
from cases.submissions import SUBMISSION_TYPE_HELPERS, get_submission_deadline
from cases.utils import decorate_orgs
from core.constants import (
    ALL_REGION_ALLOWED_TYPE_IDS,
    SECURITY_GROUP_TRA_HEAD_OF_INVESTIGATION,
    SECURITY_GROUP_TRA_LEAD_INVESTIGATOR,
    SECURITY_GROUPS_TRA,
    SECURITY_GROUP_TRA_ADMINISTRATOR,
    SECURITY_GROUPS_TRA_ADMINS,
    SECURITY_GROUP_ORGANISATION_OWNER,
    SUBMISSION_TYPE_QUESTIONNAIRE,
    SUBMISSION_TYPE_APPLICATION,
    SUBMISSION_NOTICE_TYPE_INVITE,
    SUBMISSION_NOTICE_TYPE_DEFICIENCY,
    CASE_ROLE_AWAITING_APPROVAL,
    CASE_ROLE_REJECTED,
    CASE_ROLE_APPLICANT,
    CASE_ROLE_PREPARING,
    DIRECTION_TRA_TO_PUBLIC,
    TRUTHFUL_INPUT_VALUES,
    REGEX_ISO_DATE,
)

from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

logger = logging.getLogger(__name__)

org_fields = json.dumps(
    {
        "Organisation": {
            "id": 0,
            "has_non_draft_subs": 0,
            "gov_body": 0,
            "has_roi": 0,
        }
    }
)


class CasesView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    template_name = "cases/cases.html"

    def get(self, request, *args, **kwargs):
        list_mode = request.GET.get("tab", "my")
        panel_layout = self.client(self.request.user).get_system_boolean("PRE_RELEASE_PANELS")
        fields = {
            "Case": {
                "id": 0,
                "user_case": 0,
                "name": 0,
                "reference": 0,
                "created_at": 0,
                "type": {
                    "name": 0,
                    "acronym": 0,
                    "colour": 0,
                    "reference": 0,
                    "applicant": {"organisation": 0, "name": 0, "id": 0},
                },
                "applicant": {
                    "organisation": {
                        "name": 0,
                        "id": 0,
                    }
                },
                "stage": {"name": 0},
                "case_status": {"next_action": 0, "next_notice_due": 0},
            }
        }

        if list_mode == "archived":
            fields = deep_update(
                fields,
                {
                    "Case": {
                        "workflow_state": {
                            "MEASURE_EXPIRY": 0,
                            "DETERMINATION_ACTIVE_DATE": 0,
                        }
                    }
                },
            )

        cases = self.client(request.user).get_cases(
            archived=list_mode == "archived",
            all_cases=list_mode == "all",
            new_cases=list_mode == "new",
            fields=json.dumps(fields),
        )
        tabs = {
            "value": list_mode,
            "tabList": [
                {"label": "Your cases", "value": "my", "sr_text": "Show your cases"},
                {"label": "Open cases", "value": "all", "sr_text": "Show open cases"},
                {
                    "label": "New applications",
                    "value": "new",
                    "sr_text": "Show new applications",
                },
                {
                    "label": "Archived",
                    "value": "archived",
                    "sr_text": "Show archived cases",
                },
            ],
        }
        template_name = self.template_name if panel_layout else "cases/cases_old.html"
        body_class = "full-width kill-footer" if panel_layout else "full-width"
        return render(
            request,
            template_name,
            {
                "body_classes": body_class,
                "cases": cases,
                "tabs": tabs,
            },
        )


class CaseBaseView(
    LoginRequiredMixin,
    GroupRequiredMixin,
    PermissionRequiredMixin,
    TemplateView,
    TradeRemediesAPIClientMixin,
):
    permission_required = []
    groups_required = SECURITY_GROUPS_TRA
    supress_nav_section = False

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            self._client = self.client(self.request.user)
        self.case_id = kwargs.get("case_id")
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.kwargs = kwargs
        self.organisation_id = kwargs.get("organisation_id")
        self.request = request
        self.user_token = request.user.token
        case_fields = json.dumps(
            {
                "Case": {
                    "id": 0,
                    "name": 0,
                    "initiated_at": 0,
                    "decision_to_initiate,name": 0,
                    "reference": 0,
                    "sequence": 0,
                    "type": 0,
                    "archived_at": 0,
                    "archive_reason": {"name": 0},
                    "submission_count": 0,
                    "participant_count": 0,
                    "stage": {"name": 0},
                    "case_status": 0,
                    "organisation": {"id": 0, "name": 0},
                }
            }
        )

        self.case = self._client.get_case(self.case_id, fields=case_fields)
        self.document_count = self._client.get_case_document_count(self.case_id)
        self.start = request.GET.get("start", 0)
        self.limit = request.GET.get("limit", 20)
        content_id = self.kwargs.get("nav_section_id")
        context = {
            "case": self.case,
            "case_id": self.case_id,
            "document_count": self.document_count,
            "content": self._client.get_case_content(self.case_id, content_id=content_id),
            "tree": self._client.get_nav_section(self.case_id, selected_content=content_id),
            "body_classes": "full-width",
            "panel_layout": self._client.get_system_boolean("PRE_RELEASE_PANELS"),
            "organisation_id": self.organisation_id,
            "submission_group_name": "submission",
            "alert": request.GET.get("alert"),
            "user": request.user,
        }
        deep_update(context, self.add_page_data())
        if context.get("redirect"):
            return redirect(context.get("redirect"))
        return render(request, self.template_name, context)

    def add_page_data(self):
        return {}

    def get_documents(self, submission=None, all_versions=None):
        result = self._client.get_submission_documents(
            self.case_id, submission.get("id"), all_versions=all_versions
        )
        all_documents = result.get("documents", [])
        deficiency_docs = result.get("deficiency_documents", [])
        if all_versions:
            # If this submission has an immediate ancestor, get the docs from that to mark status
            docs_by_submission = deep_index_items_by(all_documents, "version")
            this_version = int(submission.get("version"))
            this_sub = docs_by_submission.get(str(this_version))
            sub_docs = this_sub[0].get("documents")
            # we have a list of the submissions that make up a family - id, version and documents.
            if this_version > 1:
                parent_sub = docs_by_submission.get(str(this_version - 1))
                parent_docs = parent_sub and parent_sub[0].get("documents")
                parent_doc_idx = {}
                for parent_doc in parent_docs:
                    doc_type = get(parent_doc, "type/name") + "|" + get(parent_doc, "name")
                    parent_doc_idx[doc_type] = parent_doc
                for document in sub_docs:
                    document["parent"] = parent_doc_idx.get(
                        get(document, "type/name") + "|" + get(document, "name")
                    )
        else:
            sub_docs = all_documents
        submission_documents = deep_index_items_by(sub_docs, "type/key")
        document_conf_index = deep_index_items_by(
            submission_documents.get("respondent", []), "confidential"
        )
        confidential = document_conf_index.get("true", [])
        confidential.sort(key=lambda cf: cf.get("name"))
        non_conf = document_conf_index.get("", [])
        doc_index = key_by(confidential, "id")
        non_conf.sort(key=lambda nc: get(get(doc_index, str(nc.get("parent_id"))), "name"))

        # Check if any docs are virusey or not checked
        counts = {}
        for document_source, document_list in submission_documents.items():
            counts[document_source] = {"virus": 0, "unscanned": 0}
            for document in document_list:
                safe = document.get("safe")
                if not safe:
                    if safe is False:
                        counts[document_source]["virus"] += 1
                    else:
                        counts[document_source]["unscanned"] += 1

        # Get the deficiency documents from the previous version if applicable
        # if submission and (submission.get('previous_version') or {}).get('deficiency_sent_at'):
        #    previous_submission =
        #    self._client.get_submission_documents
        #    (self.case_id, submission['previous_version']['id'])
        #    deficiency_documents = [
        #        pdoc for pdoc in previous_submission.get('documents', [])
        #        if pdoc['type']['key'] == 'deficiency'
        #    ]
        return {
            "caseworker": submission_documents.get("caseworker", []),
            "respondent": submission_documents.get("respondent", []),
            "loa": submission_documents.get("loa", []),
            "deficiency": deficiency_docs,
            "confidential": confidential,
            "nonconfidential": non_conf,
            "counts": counts,
        }

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        perms = self.get_permission_required()
        return not perms or self.request.user.has_perms(perms)


class CaseAdminView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    permission_required = ("case_admin",)
    template_name = "cases/admin.html"

    def add_page_data(self):
        case_enums = self._client.get_all_case_enums()
        case_users = self._client.get_case_users(self.case["id"])
        context = {
            "case_enums": case_enums,
            "case": self.case,
            "users": case_users,
            "participants": self._client.get_case_participants(self.case_id),
        }
        return context

    def post(self, request, case_id, *args, **kwargs):
        action = request.POST.get("action")
        case = self._client.get_case(case_id)
        update_spec = {}
        if action == "initiation_flag_toggle":
            if case["initiated_at"]:
                update_spec["initiated_at"] = ""
            else:
                update_spec["initiated_at"] = timezone.now()
        elif action == "set_case_stage":
            update_spec["ignore_flow"] = request.POST.get("ignore_flow") or "false"
            update_spec["stage_id"] = request.POST.get("stage_id")
        elif action == "set_name":
            update_spec["name"] = request.POST.get("name")
        elif action == "set_case_type":
            update_spec["stage_id"] = ""
            update_spec["type_id"] = request.POST.get("type_id")
        elif action == "toggle_archived":
            if case.get("archived_at"):
                update_spec["archived_at"] = ""
            else:
                update_spec["archived_at"] = timezone.now()
                update_spec["archive_reason_id"] = request.POST.get("archive_reason_id")
        elif action == "reset_initiation_decision":
            update_spec["reset_initiation_decision"] = True
        if update_spec:
            response = self._client.update_case(case_id, update_spec)
        return redirect(f"/case/{case_id}/admin/")


class CaseMilestoneDatesView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    permission_required = ("case_admin",)
    template_name = "cases/milestone_dates.html"

    def add_page_data(self):
        case_enums = self._client.get_all_case_enums(self.case_id)
        case_milestones = self._client.case_milestones(self.case["id"])
        existing_keys = [cm["key"] for cm in case_milestones]
        context = {
            "milestone_types": case_enums.get("milestone_types"),
            "available_review_types": case_enums.get("available_review_types"),
            "milestones": case_milestones,
            "existing_milestones": existing_keys,
        }
        return context

    def post(self, request, case_id, milestone_key=None):
        milestone_key = milestone_key or request.POST.get("milestone_key")
        date = request.POST.get("date")
        response = self._client.set_case_milestone(case_id, milestone_key, date)
        return redirect(f"/case/{case_id}/milestones/")


class CaseView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    permission_required = []
    template_name = "cases/case.html"

    extra_case_fields = json.dumps(
        {
            "Case": {
                "applicant": {
                    "organisation": {
                        "id": 0,
                        "name": 0,
                        "primary_contact": {
                            "name": 0,
                            "email": 0,
                            "phone": 0,
                            "address": 0,
                            "post_code": 0,
                            "country": {"name": 0},
                            "has_user": 0,
                            "user": {"id": 0, "organisation": {"id": 0, "name": 0}},
                        },
                    }
                },
                "parent": {"id": 0, "name": 0, "reference": 0, "type": 0},
                "workflow_state": {"LINKED_CASE_CONFIRM": 0},
                "initiated_sequence": 0,
            }
        }
    )

    def add_page_data(self):

        team = self._client.get_case_team_members(self.case_id)
        team_by_group = index_users_by_group([member.get("user") for member in team])
        group_order = [
            SECURITY_GROUP_TRA_ADMINISTRATOR,
            SECURITY_GROUP_TRA_HEAD_OF_INVESTIGATION,
            SECURITY_GROUP_TRA_LEAD_INVESTIGATOR,
        ]
        case_extras = self._client.get_case(self.case_id, fields=self.extra_case_fields)
        return {
            "audit": self._client.get_audit(
                case_id=self.case_id, start=0, limit=20, milestone=True
            ),
            "case_page": True,
            "case": case_extras,
            "team_groups": team_by_group,
            "group_order": group_order,
            "public_base_url": settings.PUBLIC_BASE_URL,
        }

    def post(self, request, case_id, *args, **kwargs):
        self._client.set_case_data(case_id, {"name": request.POST.get("name")})
        redirect = request.POST.get("redirect")
        if redirect:
            return redirect(request.POST.get("redirect"))
        else:
            return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")


class PartiesView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/parties.html"

    def add_page_data(self):
        parties = []
        roles = self._client.get_case_roles()
        all_case_invites = self._client.get_contact_case_invitations(self.case_id)
        all_participants = self._client.get_case_participants(self.case_id, fields=org_fields)
        case_invites = deep_index_items_by(all_case_invites, "contact/id")
        invited = set([])
        accepted = set([])
        for invite in all_case_invites:
            org_id = invite.get("organisation", {}).get("id")
            if invite.get("accepted_at"):
                # note: accepted and invited are mutually exclusive
                accepted.add(org_id)
            else:
                invited.add(org_id)
        for role in roles:
            _base = all_participants[role["key"]]
            _base["key"] = role["key"]
            _base["name"] = role["plural"]
            if role["allow_cw_create"]:
                _base["add_link"] = f"Add {role['name']}"
            parties.append(_base)

        return {
            "party_types": parties,
            "invites": case_invites,
            "accepted_orgs": list(accepted),
            "invited_orgs": list(invited),
            "pre_release_invitations": self._client.get_system_boolean("PRE_RELEASE_INVITATIONS"),
            "alert": self.request.GET.get("alert"),
        }


class CaseTeamView(CaseBaseView):
    permission_required = "can_assign_team"
    template_name = "cases/team.html"

    def add_page_data(self):
        all_users = self._client.get_all_users(group_name="caseworker")
        users_by_group = index_users_by_group(all_users)
        team = self._client.get_case_team_members(self.case_id)
        return {
            "team": [member.get("user", {}).get("id") for member in team],
            "tra_users": all_users,
            "grouped_users": users_by_group,
            "groups": SECURITY_GROUPS_TRA[1:],
            "inactive_user_count": sum(user["active"] is False for user in all_users),
            "singleton_groups": [
                SECURITY_GROUP_TRA_HEAD_OF_INVESTIGATION,
                SECURITY_GROUP_TRA_ADMINISTRATOR,
            ],
        }

    def post(self, request, case_id, *args, **kwargs):
        user_ids = request.POST.getlist("user_id")
        response = self._client.assign_case_team(case_id, user_ids)
        return redirect(f"/case/{case_id}/")


class SubmissionsView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/submissions.html"
    show_global = False
    sub_page = ""

    def get_tab(self, role, party):
        if not role.get("allow_cw_create"):
            return role["key"]
        return "sampled" if party.get("sampled") else "not_sampled"

    def consolidate_submissions(
        self, case, participants, submissions_by_party, counts, selected_tab
    ):
        roles = []
        single_role_return = None  # for awaiting and rejected - only return that specific role
        for role in self._client.get_case_roles():
            role["participants"] = []
            for party in participants.get(role["key"], {}).get("parties", []):
                tab = self.get_tab(role, party)
                submissions = submissions_by_party.get(party["id"], [])

                submissions += submissions_by_party.get("", [])
                if submissions:
                    counts[tab] = counts.get(tab, 0) + len(submissions)
                    if tab == selected_tab:
                        party["submissions"] = submissions
                        role["participants"].append(party)
                        if not party.get("gov_body"):
                            role["customer_parties"] = True
            sort_key = (
                "submissions/0/received_at"
                if selected_tab == CASE_ROLE_AWAITING_APPROVAL
                else "name"
            )
            role["participants"].sort(key=lambda pt: get(pt, sort_key) or "")
            if role.get("key") == selected_tab:
                single_role_return = role
            if role.get("allow_cw_create"):
                roles.append(role)
        return [single_role_return] if single_role_return else roles

    def get_name(self, participant):
        return participant.get("name")

    def flatten_participants(self, source):
        participants = []
        for role in source:
            rec = source[role]
            participants = participants + rec["parties"]
        participants.sort(key=self.get_name)
        return participants

    def divide_submissions(self, submissions):
        incoming = []
        outgoing = []
        draft = []

        for submission in submissions:
            if get(submission, "status/sent"):
                outgoing.append(submission)
            elif get(submission, "status/default") and get(submission, "type/direction") != 1:
                draft.append(submission)
            else:
                if (
                    not get(submission, "status/draft")
                    or get(submission, "type/key") == "application"
                ):  # customer draft should not be seen by investigators
                    incoming.append(submission)
        return {
            "incoming": sorted(incoming, key=lambda su: su.get("received_at") or "", reverse=True),
            "outgoing": sorted(outgoing, key=lambda su: su.get("sent_at") or "", reverse=True),
            "draft": sorted(draft, key=lambda su: su.get("created_at") or "", reverse=True),
        }

    def add_page_data(self):
        sampled_only = self.request.GET.get("sampled", "true") in TRUTHFUL_INPUT_VALUES
        tab = self.request.GET.get("tab", "sampled").lower()
        roles = self._client.get_case_roles()
        submission_fields = json.dumps(
            {
                "Submission": {
                    "id": 0,
                    "name": 0,
                    "type": {"name": 0},
                    "version": 0,
                    "status": {"name": 0, "draft": 0, "default": 0},
                    "sent_at": 0,
                    "received_at": 0,
                    "created_at": 0,
                    "due_at": 0,
                    "tra_editable": 1,
                    "organisation": {"id": 0},
                }
            }
        )

        all_submissions = self._client.get_submissions(self.case_id, show_global=True)
        submissions_by_type = deep_index_items_by(all_submissions, "type/name")

        # Get submissions that have just been created by customer
        # or are still in draft after creation
        draft_submissions = deep_index_items_by(all_submissions, "status/default").get("true") or []
        # Remove any that are back with the customer following deficiency
        draft_first_version_submissions = (
            deep_index_items_by(draft_submissions, "version").get("1") or []
        )
        # Exclude these drafts from our list
        non_draft_submissions = [
            sub for sub in all_submissions if sub not in draft_first_version_submissions
        ]
        # draft applications are included to allow a heads up view
        # to the caseworker before it's submitted
        if submissions_by_type.get("application", [{}])[0].get("status", {}).get("default") is True:
            submissions_by_type["application"][0]["tra_editable"] = True
            non_draft_submissions += submissions_by_type["application"]
        submissions_by_party = deep_index_items_by(non_draft_submissions, "organisation/id")

        for submission in non_draft_submissions:
            new_submission = False
            for document_type, documents in self.get_documents(submission=submission).items():
                if document_type in ["nonconfidential", "confidential"]:
                    for document in documents:
                        if (
                            not document["deficient"]
                            and not document["sufficient"]
                            and document["safe"]
                        ):
                            new_submission = True
            submission["new_submission"] = new_submission

        case_enums = self._client.get_all_case_enums()
        invites = self._client.get_case_invite_submissions(self.case_id)
        participants = self._client.get_case_participants(self.case_id, fields=org_fields)
        flat_participants = self.flatten_participants(participants)
        counts = {}
        if self.sub_page:
            self.template_name = f"cases/submissions_{self.sub_page}.html"
            tab = self.request.GET.get("tab", "incoming").lower()
        elif self._client.get_system_boolean("PRE_NEW_SUBMISSION_PAGE"):
            self.template_name = "cases/submissions_new.html"

        context = {
            "raw_participants": participants,
            "submissions": submissions_by_type,
            "participants": flat_participants,
            "counts": counts,
            "all_roles": self.consolidate_submissions(
                self.case,
                participants=participants,
                submissions_by_party=submissions_by_party,
                counts=counts,
                selected_tab=tab,
            ),
            "submission_types": case_enums["case_worker_allowed_submission_types"],
            "invites": invites,
            "tab": tab,
            "submission_groups": self.divide_submissions(all_submissions),
            "all_submissions": all_submissions,
        }
        # TODO: Temp handling of application vs ex_officio ones
        if not submissions_by_type.get("application") and submissions_by_type.get(
            "ex officio application"
        ):
            context["submissions"]["application"] = submissions_by_type["ex officio application"]
        return context


class SubmissionView(CaseBaseView):
    """
    View and modify submissions
    """

    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/submission.html"

    extra_case_fields = json.dumps(
        {
            "Case": {
                "applicant": 0,
                "product": 0,
                "sources": 0,
            }
        }
    )

    def add_page_data_old(self):
        alert = self.request.GET.get("alert")  # indicates the submission has just been created
        documents = []
        submission = {}
        submission_id = self.kwargs.get("submission_id")
        third_party_invite = False
        if submission_id:
            submission = self._client.get_submission(self.case_id, submission_id)
            submission_type = submission["type"]
            third_party_invite = submission_type["name"] == "Invite 3rd party"
            self.organisation_id = submission["organisation"]["id"]
            created_by_id = get(submission, "created_by/id")
            if created_by_id:
                full_user = self._client.get_user(created_by_id)
                submission["created_by"]["organisation"] = get(full_user, "organisations/0")
        submission_context = {}
        if SUBMISSION_TYPE_HELPERS.get(submission_type["key"]):
            submission_context = SUBMISSION_TYPE_HELPERS[submission_type["key"]](
                submission, self.request.user
            ).get_context()
        self.template_name = "cases/submission.html"
        case_extras = self._client.get_case(self.case_id, fields=self.extra_case_fields)
        context = {
            "submission": submission,
            "template_name": f"{submission_type['key']}",
            "documents": self.get_documents(submission=submission, all_versions=True),
            "alert": alert,
            "case": case_extras,
            "third_party_invite": third_party_invite,
            **submission_context,
        }
        if (
            not submission
            or not submission.get("status")
            or submission.get("status", {}).get("default")
        ):
            context["mode"] = "form"
        else:
            context["mode"] = "view"
        if self.organisation_id:
            self.organisation = self._client.get_organisation(self.organisation_id)
            context["organisation"] = self.organisation
            context["organisation_id"] = str(self.organisation["id"])
        return context

    def get_all_participants(self, case_participants):
        all_parties = []
        roles = {}
        for type_name, role_parties in case_participants.items():
            parties = role_parties.get("parties")
            if parties:
                all_parties.extend(parties)
                role = parties[0].get("role")
                roles[role.get("key")] = role

        return deep_index_items_by(all_parties, "sampled"), roles

    def add_page_data(self):
        case_enums = self._client.get_all_case_enums()
        submission = {}
        participants = self._client.get_case_participants(self.case_id, fields=org_fields)
        parties, roles = self.get_all_participants(participants)
        alert = self.request.GET.get("alert")  # indicates the submission has just been created
        submission_id = self.kwargs.get("submission_id")
        if submission_id:
            submission = self._client.get_submission(self.case_id, submission_id)
            json_data = from_json(submission.get("deficiency_notice_params"))
            _default = (submission.get("status") or {}).get("default")
            if not (_default) or (
                _default and submission["type"]["id"] == SUBMISSION_TYPE_APPLICATION
            ):
                return self.add_page_data_old()
            self.organisation_id = submission["organisation"]["id"]

            ret = {
                "roles": roles,
                "submission": submission,
                "status": (submission.get("status") or {}).get("id"),
                "alert": alert,
                "documents": self.get_documents(submission=submission),
                "role": submission.get("organisation_case_role") or {"name": "Public file"},
                "participants": participants,
                "all_participants": parties,
                "json_data": json_data,
                "selected_submission_type": submission.get("type", {}).get("key")
                or "questionnaire",
            }
        else:
            role = self.request.GET.get("for")
            sampled = self.request.GET.get("sampled") == "sampled"
            full_role = (
                self._client.get_case_role(role)
                if (role and role != "public")
                else {"name": "Public file"}
            )
            case_enums = self._client.get_all_case_enums(direction=DIRECTION_TRA_TO_PUBLIC)
            # Get all draft submissions of this type
            all_submissions = self._client.get_submissions(self.case_id, show_global=True)
            draft_submissions = (
                deep_index_items_by(all_submissions, "status/default").get("true") or []
            )
            # draft_submissions_this_role = deep_index_items_by(draft_submissions,
            # 'organisation_case_role/key').get('' if role == 'public' else role)
            draft_submissions_this_role = deep_index_items_by(
                draft_submissions, "organisation_id"
            ).get("")

            ret = {
                "submission": submission,
                "submission_type_id": self.kwargs.get("submission_type_id")
                or self.request.GET.get("submission_type_id"),
                "submission_statuses": case_enums["submission_statuses"],
                "statuses_by_type": case_enums["statuses_by_type"],
                "selected_submission_type": self.request.GET.get("submission_type")
                or "questionnaire",
                "organisation_id": self.kwargs.get("organisation_id"),
                "draft_submissions": draft_submissions_this_role,
                "role": full_role,
            }
            if role == "public":
                ret.update(
                    {
                        "submission_types": case_enums["public_submission_types"],
                        "public": True,
                        "organisation_id": self.kwargs.get("organisation_id"),
                    }
                )
            else:
                role_participants = participants.get(role, {}).get("parties", [])
                filtered = list(
                    filter(
                        lambda party: party
                        if party.get("sampled") == sampled and not party.get("gov_body")
                        else None,
                        role_participants,
                    )
                )

                ret.update(
                    {
                        "submission_types": case_enums["case_worker_allowed_submission_types"],
                        "participants": participants,
                        "roles": roles,
                    }
                )
            self.organisation_id = self.organisation_id or self.request.GET.get("organisation_id")
        if self.organisation_id:
            self.organisation = self._client.get_organisation(self.organisation_id)
            ret["organisation"] = self.organisation
            ret["organisation_id"] = str(self.organisation["id"])
        # add errors from the url
        errors = self.request.GET.get("errors")
        if errors:
            try:
                ret["errors"] = json.loads(errors)
            except Exception as ex:
                pass
        # Set up template to use
        template_name = (
            submission["type"]["key"]
            if submission
            else (role if role == "public" else "questionnaire")
        )
        ret.update({"template_name": template_name, "mode": "form"})
        return ret

    def post(  # noqa: C901
        self,
        request,
        case_id,
        submission_id=None,
        organisation_id=None,
        *args,
        **kwargs,
    ):
        """
        Update an existing submission
        """
        return_data = {"submission_id": str(submission_id)}
        contact_id = request.POST.get("contact_id")
        btn_value = request.POST.get("btn-value")
        review = request.POST.get("review")
        name = request.POST.get("name")
        due_at = request.POST.get("due_at")
        response_window_yn = request.POST.get("response_window_yn")
        time_window = request.POST.get("time_window")

        meta_raw = request.POST.getlist("meta")
        meta = [json.loads(block) for block in meta_raw]
        file_details = deep_index_items_by(meta, "name")
        file_details_by_id = deep_index_items_by(meta, "file/id")

        organisation_id = organisation_id or request.POST.get("organisation_id")
        send_to = request.POST.get("send_to")
        submission = self._client.get_submission(case_id, submission_id)
        organisation_id = submission.get("organisation", {}).get("id")
        status_id = request.POST.get("submission_status_id")
        if submission_id and btn_value == "discard":
            delete_submission_response = self._client.delete_submission(
                case_id=case_id, submission_id=submission_id
            )
            return HttpResponse(
                json.dumps({"redirect_url": f"/case/{case_id}/submissions/"}),
                content_type="application/json",
            )
        # check if the update is for name or notify contact
        if (
            submission["name"] != name
            or not submission["contact"]
            or submission.get("contact", {}).get("id") != contact_id
        ):
            if name is not None and not name:
                return_data.update({"errors": '{"name":"You must enter a name"}'})
            if due_at and not re.match(REGEX_ISO_DATE, due_at):
                return_data.update({"errors": '{"due_date":"Invalid date"}'})
            if not return_data.get("errors"):
                self._client.update_submission(
                    case_id=case_id,
                    submission_id=submission_id,
                    name=name,
                    contact_id=contact_id,  # TODO:not used
                    due_at=due_at,
                    time_window=time_window,
                    description=request.POST.get("description"),
                    url=request.POST.get("url"),
                )
                # API `update_submission` returns an incomplete submission
                # (no documents) so we re-fetch the submission here.
                submission = self._client.get_submission(case_id, submission_id)
                return_data.update({"submission": submission})
        if submission.get("id"):

            for _file in request.FILES.getlist("files"):
                original_file_name = _file.original_name
                details = file_details.get(original_file_name.lower())[0]
                confidential = details.get("confidential")
                document_type = details.get("submission_document_type")
                try:
                    document = self._client.upload_document(
                        case_id=str(case_id),
                        submission_id=submission_id,
                        organisation_id=str(organisation_id),
                        data={
                            "name": "Questionnaire",
                            "confidential": confidential,
                            "submission_document_type": document_type,
                            "document_name": original_file_name,
                            "file_name": _file.name,
                            "file_size": _file.file_size,
                        },
                    )
                except Exception as ex:
                    return HttpResponse(
                        json.dumps(
                            {
                                "redirect_url": f"/case/{case_id}/submission/{submission_id}/edit/?error=up"  # noqa: E301,E501
                            }
                        ),
                        content_type="application/json",
                    )

            case_files = request.POST.getlist("case_files")
            if case_files:
                for case_file_id in case_files:
                    details = (file_details_by_id.get(case_file_id) or [])[0]
                    document = self._client.attach_document(
                        case_id=str(case_id),
                        submission_id=submission_id,
                        organisation_id=str(organisation_id),
                        data={"submission_document_type": details.get("submission_document_type")},
                        document_id=case_file_id,
                    )
            submission_group_name = get(submission, "type/key")
            if btn_value in ["send", "publish", "withdraw"]:
                if btn_value in ["publish", "withdraw"]:
                    result = self._client.set_submission_state(
                        case_id,
                        submission_id,
                        "sent"
                        if (btn_value == "send" or submission_group_name == "public")
                        else "",
                        {"publish": "issue", "withdraw": "un-issue"}[btn_value],
                    )
                    result = self._client.update_submission(
                        case_id=case_id, submission_id=submission_id
                    )
                return_data.update(
                    {
                        "redirect_url": f"/case/{case_id}/submission/{submission['id']}/?alert={btn_value}"  # noqa: E301, E501
                    }
                )

            if btn_value == "sufficient":
                # Set the submission to sufficient
                result = self._client.set_submission_state(case_id, submission_id, btn_value)
                return_data.update({"alert": "Submission approved"})
                submission_type = submission["type"]
                type_helpers = SUBMISSION_TYPE_HELPERS.get(submission_type["key"])
                if type_helpers:
                    return_data.update(
                        type_helpers(submission, self.request.user).on_approve() or {}
                    )

            # Update submission document approvals
            self.update_submission_status(request.POST, submission)

            # set any deficiency-notice parameters
            updated = False
            deficiency_notice_params = from_json(submission.get("deficiency_notice_params"))
            send_to = request.POST.getlist("send_to")
            if send_to:
                deficiency_notice_params["send_to"] = send_to
                updated = True

            regex = r"^deficiency_notice_params_"
            for param_key in request.POST:
                matches = re.split(regex, param_key)
                if len(matches) > 1:
                    value = request.POST[param_key]
                    updated = updated or (deficiency_notice_params.get(matches[1]) != value)
                    if value == "__remove":
                        if get(deficiency_notice_params, matches[1]):
                            deficiency_notice_params.pop(matches[1])
                    else:
                        deficiency_notice_params[matches[1]] = value
            if updated:
                update_submission_response = self._client.update_submission(
                    case_id=case_id,
                    submission_id=submission_id,
                    deficiency_notice_params=to_json(deficiency_notice_params),
                )
            if btn_value == "save-exit":
                return_data.update({"redirect_url": f"/case/{case_id}/submissions"})
                if deficiency_notice_params:
                    return_data.update(
                        {"redirect_url": f"/case/{case_id}/submission/{submission_id}"}
                    )
        return HttpResponse(json.dumps(return_data), content_type="application/json")

    def update_submission_status(self, request_params, submission):
        """Update submission document statuses.

        For each document in the submission review, examine response to
        establish if it was marked sufficient/deficient. Call API to update
        submission document status if it has changed.

        :param (dict) request_params: request parameters
        :param (dict) submission: submission
        """
        submission_docs = {doc["id"]: doc for doc in submission.get("documents")}
        for doc_id in request_params:
            if doc_id in submission_docs:
                current_status = submission_docs[doc_id]["sufficient"]
                new_status = request_params[doc_id] == "yes"
                if current_status != new_status:
                    self._client.set_submission_document_state(
                        case_id=submission["case"]["id"],
                        submission_id=submission.get("id"),
                        document_id=doc_id,
                        status="sufficient" if new_status else "deficient",
                        block_from_public_file=submission_docs.get("block_from_public_file"),
                        block_reason=submission_docs.get("block_reason"),
                    )


class SubmissionCreateView(SubmissionView):
    groups_required = SECURITY_GROUPS_TRA

    def post(self, request, case_id, *args, **kwargs):
        btn_value = request.POST.get("btn-value")
        send_to = request.POST.getlist("send_to")
        organisation_id = request.POST.get("organisation_id")

        submission_data = {
            "submission_type": int(
                request.POST.get("submission_type_id", SUBMISSION_TYPE_QUESTIONNAIRE)
            ),
            "case_id": str(case_id),
            "organisation_id": str(organisation_id) if organisation_id else None,
            "contact_id": request.POST.getlist("contact_id"),
            "public": request.POST.get("public"),
        }
        if send_to:
            submission_data["deficiency_notice_params"] = to_json(
                {"send_to": send_to, "case_role": request.POST.get("role_key")}
            )
        result = self._client.create_submission(**submission_data)
        submission = result.get("submission", {}) if result else {}

        return HttpResponse(
            json.dumps(
                {
                    "submission_id": submission.get("id"),
                    "redirect_url": f"/case/{case_id}/submission/{submission['id']}/",
                }
            ),
            content_type="application/json",
        )


class SubmissionDocumentView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA

    def post(self, request, case_id, submission_id, organisation_id=None, *args, **kwargs):
        btn_value = request.POST.get("btn-value")
        response = {}
        error_message = None
        files = request.FILES.getlist("file")
        document_list_json = request.POST.get("document_list")

        if document_list_json:
            document_list = json.loads(document_list_json)

            for doc_id, doc_status in document_list.items():
                logger.debug(f"update document state {doc_id}")
                response = self._client.set_submission_document_state(
                    case_id=case_id,
                    submission_id=submission_id,
                    document_id=doc_id,
                    status=doc_status["status"],
                    block_from_public_file=doc_status["block_from_public_file"],
                    block_reason=doc_status["block_reason"],
                )

        if files:
            redirect_to = request.POST.get("next", f"/case/{case_id}/submission/{submission_id}/")
            for _file in files:
                data = {
                    "submission_document_type": request.POST.get("submission_document_type"),
                    "document_name": _file.original_name,
                    "file_name": _file.name,
                    "file_size": _file.file_size,
                }
                try:
                    response = self._client.upload_document(
                        data=data,
                        organisation_id=organisation_id,
                        case_id=case_id,
                        submission_id=submission_id,
                    )
                except Exception as ex:
                    error_message = str(ex)
                    try:
                        error_message = ex.response.json().get("detail")
                    except AttributeError:
                        pass
            if error_message:
                redirect_to += f"?error={error_message}"
        return HttpResponse(json.dumps(response), content_type="application/json")

    def delete(self, request, case_id, submission_id, document_id, *args, **kwargs):
        response = self._client.detach_document(
            case_id=case_id, submission_id=submission_id, document_id=document_id
        )
        return HttpResponse(json.dumps(response), content_type="application/json")


class SubmissionStatusView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA

    def post(self, request, case_id, submission_id, *args, **kwargs):
        stage_change_if_sufficient = request.POST.get("stage_change_if_sufficient")
        stage_change_if_deficient = request.POST.get("stage_change_if_deficient")
        submission = self._client.get_submission(case_id, submission_id)
        status_id = request.POST.get("submission_status_id")
        if submission.get("status", {}).get("id") != status_id:
            status_response = self._client.set_submission_status(
                case_id=case_id,
                submission_id=submission_id,
                status_id=status_id,
                stage_change_if_sufficient=stage_change_if_sufficient,
                stage_change_if_deficient=stage_change_if_deficient,
                deficiency_documents=request.FILES.getlist("deficiency_document"),
                issue=request.POST.get("issue"),
            )

            if status_response.get("submission"):
                submission_id = status_response["submission"]["id"]
        return redirect(f"/case/{case_id}/submission/{submission_id}/")


class SubmissionApprovalView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/submission.html"

    def add_page_data(self):
        submission_id = self.kwargs.get("submission_id")
        submission = self._client.get_submission(self.case_id, submission_id)
        sub_documents = self._client.get_submission_documents(self.case_id, submission_id)
        documents = sub_documents.get("documents", [])
        submission.update(sub_documents)
        case_enums = self._client.get_all_case_enums()
        submission_type_id = submission["type"]["id"]
        status_map = case_enums["submission_status_map"]
        status_options = status_map.get(str(submission_type_id), {}).get("keys", [])
        status_context = status_map.get(str(submission_type_id))
        submission_documents = self.get_documents(submission=submission)
        context = {
            "template_name": submission["type"]["key"],
            "mode": "approval",
            "submission": submission,
            "case_enums": case_enums,
            "status_context": status_context,
            "documents": submission_documents,
        }
        return context


class SubmissionDeficiencyView(CaseBaseView):
    """
    Set the submission into a deficiency status and notify the party about it.
    """

    groups_required = SECURITY_GROUPS_TRA
    raise_exception = True

    def get(self, request, case_id, submission_id, *args, **kwargs):
        submission = self._client.get_submission(case_id, submission_id)
        submission_type = submission["type"]
        contact = submission_contact(submission)
        contact_name = contact.get("name")
        organisation_name = submission.get("organisation", {}).get("name") or (
            contact.get("organisation") or {}
        ).get("name")
        notification_template = self._client.get_notification_template(
            "NOTIFY_SUBMISSION_DEFICIENCY"
        )
        template_name = f"cases/submissions/{submission_type['key']}/notify.html"
        due_at = get_submission_deadline(submission, settings.FRIENDLY_DATE_FORMAT)
        values = {
            "full_name": contact_name,
            "case_name": submission["case"]["name"],
            "case_number": submission["case"]["reference"],
            "company_name": organisation_name,
            "deadline": due_at or "No deadline assigned",
            "submission_type": submission.get("type", {}).get("name"),
            "login_url": public_login_url(),
            "footer": self._client.get_system_parameters("NOTIFY_BLOCK_FOOTER")["value"],
        }
        context = {
            "form_action": f"/case/{case_id}/submission/{submission_id}/status/notify/",
            "form_title": f"Deficiency Notice for {organisation_name}",
            "cancel_redirect_url": f"/case/{case_id}/submission/{submission_id}/",
            "editable_fields": {  # leaving one as a future example
                # 'full_name': {'title': 'Name'},
            },
            "notification_template": notification_template,
            "submission": submission,
            "case_id": str(case_id),
            "contact": contact,
            "values": values,
            "parsed_template": parse_notify_template(notification_template["body"], values),
        }
        return render(request, template_name, context)

    def post(self, request, case_id, submission_id, *args, **kwargs):
        stage_change_if_sufficient = request.POST.get("stage_change_if_sufficient")
        stage_change_if_deficient = request.POST.get("stage_change_if_deficient")
        submission = self._client.get_submission(case_id, submission_id)
        notify_keys = [
            "full_name",
            "case_name",
            "case_number",
            "company_name",
            "deadline",
            "submission_type",
            "login_url",
        ]
        notify_data = {key: request.POST.get(key) for key in notify_keys}
        if request.POST.get("contact_id"):
            notify_data["contact_id"] = request.POST["contact_id"]

        case_enums = self._client.get_all_case_enums()

        submission_type_id = submission["type"]["id"]
        status_map = case_enums["submission_status_map"]
        status_context = status_map.get(str(submission_type_id))
        status_id = status_context.get("NO")
        error = None
        if status_id:
            if submission.get("status", {}).get("id") != status_id:
                status_response = self._client.set_submission_status(
                    case_id=case_id,
                    submission_id=submission_id,
                    status_id=status_id,
                    stage_change_if_sufficient=stage_change_if_sufficient,
                    stage_change_if_deficient=stage_change_if_deficient,
                )
                self._client.submission_notify(
                    case_id=case_id,
                    organisation_id=submission["organisation"]["id"],
                    submission_id=submission["id"],
                    values=notify_data,
                    notice_type=SUBMISSION_NOTICE_TYPE_DEFICIENCY,
                )
                # reset the submission id to redirect to the new clone if available
                if status_response.get("submission"):
                    submission_id = status_response["submission"]["id"]
            return HttpResponse(
                json.dumps(
                    {
                        "redirect_url": f"/case/{case_id}/submission/{submission_id}/",
                    }
                ),
                content_type="application/json",
            )
        # If there's no deficiency state for this submission type, return an error
        return HttpResponse(
            json.dumps(
                {
                    "error": "No deficiency status for this submission type",
                }
            ),
            content_type="application/json",
        )


class SubmissionVerifyBaseView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA

    def get_submission_id(self, case_id=None, organisation_id=None):
        submission_id = self.kwargs.get("submission_id")
        if not submission_id:
            # If this is called from the party page - there is no submission id
            # so find from the org/case
            submissions = self._client.get_submissions_public(
                organisation_id=organisation_id,
                case_id=case_id,
                fields=json.dumps({"id": 0, "type": {"key": 0}}),
            )
            for submission in submissions:
                if get(submission, "type/key") in ["interest", "application"]:
                    submission_id = submission.get("id")
                    break  # we only want one reg-of-interest submission
        return submission_id

    def update_submission_json(self, case_id, submission, params):
        regex = r"^deficiency_notice_params_"
        deficiency_notice_params = submission.get("deficiency_notice_params") or {}
        updated = False
        response = None
        for param_key in params:
            matches = re.split(regex, param_key)
            if len(matches) > 1:
                value = params[param_key]
                updated = updated or (deficiency_notice_params.get(matches[1]) != value)
                deficiency_notice_params[matches[1]] = value
        if updated:
            response = self._client.update_submission(
                case_id=case_id,
                submission_id=get(submission, "id"),
                deficiency_notice_params=to_json(deficiency_notice_params),
            )
        return response


class SubmissionVerifyViewTasks(SubmissionVerifyBaseView):
    """
    Used to verify user and orgs admission to a case
    """

    template_name = "cases/verify/submission_verify_tasks.html"
    submission_fields = json.dumps(
        {
            "Submission": {
                "id": 0,
                "deficiency_notice_params": 0,
                "organisation": {
                    "id": 0,
                    "name": 0,
                },
                "contact": {
                    "name": 0,
                    "email": 0,
                    "user": {
                        "name": 0,
                        "email": 0,
                        "id": 0,
                        "organisation": {
                            "organisation": {
                                "id": 0,
                                "name": 0,
                            }
                        },
                    },
                    "organisation": {
                        "id": 0,
                        "name": 0,
                    },
                },
                "case": 0,
                "type": 0,
                "created_by": 0,
                "organisation_case_role_outer": 0,
            }
        }
    )

    def get(self, request, case_id, organisation_id, **kwargs):
        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        if not submission_id:
            return HttpResponse(
                json.dumps(
                    {
                        "error": "You cannot verify this organisation "
                        "as they have not yet registered interest in this case.",
                    }
                ),
                content_type="application/json",
            )
        submission = self._client.get_submission(
            self.case_id, submission_id, fields=self.submission_fields
        )
        json_data = submission.get("deficiency_notice_params") or {}
        organisation = submission.get("organisation")
        caserole = self._client.get_organisation_case_role(
            case_id=case_id, organisation_id=get(submission, "organisation/id")
        )
        org_matches = self._client.get_organisation_matches(organisation_id, with_details="none")

        return render(
            request,
            self.template_name,
            {
                "submission": submission,
                "organisation": organisation,
                "caserole": caserole,
                "org_matches": org_matches,
                "page_data": {
                    "submission": submission,
                    "organisation": organisation,
                },
            },
        )


class SubmisisonVerifyEditLoaView(SubmissionVerifyBaseView):
    def get(self, request, case_id, organisation_id):
        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        submission = self._client.get_submission(case_id, submission_id)

        organisation = self._client.get_organisation(
            case_id=case_id, organisation_id=organisation_id
        )
        documents = self.get_documents(submission)
        caserole = self._client.get_organisation_case_role(
            case_id=self.case_id, organisation_id=organisation_id
        )
        org_contacts = self._client.get_organisation_contacts(
            organisation_id, case_id, exclude_indirect=True
        )

        return render(
            request,
            "cases/verify/loa.html",
            {
                "auth_contacts": org_contacts,
                "organisation": organisation,
                "documents": documents,
                "LOA": caserole.get("auth_contact"),
                "submission": submission,
            },
        )

    def post(self, request, case_id, organisation_id, *args, **kwargs):
        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        submission = self._client.get_submission(case_id, submission_id)
        self.update_submission_json(case_id, submission, request.POST)
        result = self._client.set_organisation_case_role_loa(
            case_id,
            organisation_id,
            pluck(
                request.POST,
                ["LOA_contact_id", "name", "email", "address", "org_name", "phone"],
            ),
        )
        return HttpResponse(json.dumps(result))


class SubmisisonVerifyOrganisation(SubmissionVerifyBaseView):
    enable_merge = False

    def get(self, request, case_id, organisation_id):
        test_org_id = request.GET.get("org_id") or organisation_id
        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        submission = self._client.get_submission(case_id, submission_id)
        organisation = self._client.get_organisation(case_id=case_id, organisation_id=test_org_id)
        if self.enable_merge:
            org_matches = self._client.get_organisation_matches(test_org_id, with_details=True)
        else:
            org_matches = self._client.get_organisation_matches(test_org_id, with_details=False)
        org_matches.sort(
            key=lambda m: 1 if m.get("id") == test_org_id else 0
        )  # put the actual match at the end
        matches = decorate_orgs(org_matches, test_org_id, exclude_case_id=case_id)
        for match in matches:
            if str(match.get("id")) == str(organisation.get("id")):
                organisation.update(match)

        return render(
            request,
            "cases/verify/merge_org.html" if self.enable_merge else "cases/verify/verify_org.html",
            {
                "case_id": self.case_id,
                "organisation": organisation,
                "match_list": matches,
                "representing": test_org_id != organisation_id,
                "json_data": submission.get("deficiency_notice_params"),
            },
        )

    def post(self, request, case_id, organisation_id, *args, **kwargs):
        test_org_id = request.POST.get("org_id") or organisation_id
        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        submission = self._client.get_submission(case_id, submission_id)
        verify = request.POST.get("deficiency_notice_params_org_verify")
        if verify == "verified":
            self._client.verify_caserole(
                case_id=case_id, organisation_id=get(submission, "organisation/id")
            )
        elif verify == "rejected":
            result = self._client.reject_organisation(case_id, organisation_id)
        result = self.update_submission_json(case_id, submission, request.POST)
        return HttpResponse(json.dumps({"result": True}))


class SubmissionVerifyAccept(SubmissionVerifyBaseView):
    def get(self, request, case_id, organisation_id):
        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        submission = self._client.get_submission(case_id, submission_id)
        organisation = self._client.get_organisation(
            case_id=case_id, organisation_id=organisation_id
        )
        caserole = self._client.get_organisation_case_role(
            case_id=self.case_id, organisation_id=organisation_id
        )
        roles = self._client.get_case_roles(
            exclude=[
                CASE_ROLE_APPLICANT,
                CASE_ROLE_AWAITING_APPROVAL,
                CASE_ROLE_REJECTED,
                CASE_ROLE_PREPARING,
            ]
        )

        return render(
            request,
            "cases/verify/accept.html",
            {
                "submission": submission,
                "organisation": organisation,
                "roles": roles,
                "caserole": caserole,
                "role_name": get(caserole, "role/name"),
            },
        )

    def post(self, request, case_id, organisation_id, *args, **kwargs):
        role_key = request.POST.get("role_key")
        result = {}
        result = self._client.set_organisation_case_role(
            case_id, organisation_id, role_key, pluck(request.POST, ["approve"])
        )
        return HttpResponse(json.dumps(result))


class SubmissionVerifyNotify(SubmissionVerifyBaseView):
    def get(self, request, case_id, organisation_id):
        caserole = self._client.get_organisation_case_role(
            case_id=self.case_id, organisation_id=organisation_id
        )
        role_name = get(caserole, "role/name")
        action = (
            "reject" if get(caserole, "role/key") == "rejected" else "accept"
        )  # Todo: get this from the right place
        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        submission = self._client.get_submission(case_id, submission_id)
        case = self._client.get_case(case_id)
        contact = submission_contact(submission)
        organisation = self._client.get_organisation(
            case_id=case_id, organisation_id=organisation_id
        )
        notify_key = (
            "NOTIFY_INTERESTED_PARTY_REQUEST_PERMITTED"
            if action == "accept"
            else "NOTIFY_INTERESTED_PARTY_REQUEST_DENIED"
        )
        try:
            notification_template = self._client.get_notification_template(notify_key)
            values = self._client.create_notify_context(
                {
                    "full_name": contact.get("name"),
                    "case_name": case.get("name"),
                    "case_number": case.get("reference"),
                    "company_name": organisation["name"],
                    "login_url": public_login_url(),
                    "role": role_name,
                }
            )
            parsed_template = parse_notify_template(notification_template["body"], values)
        except Exception as ex:
            parsed_template = ""
        # contacts for the notification contact selector
        contacts = organisation.get("contacts", [])
        user = self._client.get_user(get(submission, "created_by/id"))
        contacts.append(user.get("contact"))

        return render(
            request,
            "cases/verify/notify.html",
            {
                "parsed_template": parsed_template,
            },
        )

    def post(self, request, case_id, organisation_id, *args, **kwargs):

        submission_id = self.get_submission_id(case_id=case_id, organisation_id=organisation_id)
        self._client.approve_submission(submission_id=submission_id)
        return HttpResponse(json.dumps({"result": True}))


class SubmissionNotifyView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    raise_exception = True

    def get(self, request, case_id, submission_id, *args, **kwargs):
        case = self._client.get_case(case_id)
        submission = self._client.get_submission(case_id, submission_id)
        json_data = from_json(submission.get("deficiency_notice_params"))
        contact = None
        contact_name = None
        send_to = json_data.get("send_to")
        if not send_to:
            contact = submission_contact(submission)
            contact_name = contact and contact.get("name")

        submission_type = submission["type"]
        notify_sys_param_name = submission_type.get("notify_template") or "NOTIFY_QUESTIONNAIRE"
        notification_template = self._client.get_notification_template(notify_sys_param_name)
        template_name = f"cases/submissions/{submission_type['key']}/notify.html"
        due_at = get_submission_deadline(submission, settings.FRIENDLY_DATE_FORMAT)

        values = {
            "full_name": contact_name,
            "case_number": case["reference"],
            "case_name": case["name"],
            "investigation_type": case["type"]["name"],
            "country": case["sources"][0]["country"] if case["sources"] else "N/A",
            "company_name": submission["organisation"].get("name"),
            "deadline": due_at or "No deadline assigned",
            "login_url": public_login_url(),
            "description": submission.get("description"),
            "submission_request_name": submission.get("name"),
            "notice_type": submission.get("type", {}).get("name"),
            "notice_url": submission["url"],
            "notice_of_initiation_url": submission["url"],
            "footer": self._client.get_system_parameters("NOTIFY_BLOCK_FOOTER")["value"],
        }

        template_list = []
        if send_to:
            for case_role, participant_list in (
                self._client.get_case_participants(case_id) or {}
            ).items():
                for participant in participant_list.get("parties"):
                    if participant.get("id") in send_to:
                        contact = participant.get("primary_contact")
                        if contact:
                            local_values = {
                                "full_name": contact.get("name"),
                                "email": contact.get("email"),
                                "company_name": participant.get("name"),
                            }
                            values.update(local_values)
                            template_list.append(
                                {
                                    "values": local_values,
                                    "preview": parse_notify_template(
                                        notification_template["body"], values
                                    ),
                                }
                            )
        else:
            template_list[contact.get("email")] = parse_notify_template(
                notification_template["body"], values
            )

        context = {
            "form_action": f"/case/{case_id}/submission/{submission_id}/notify/",
            "form_title": f"Invite {contact_name}",
            "cancel_redirect_url": f"/case/{case_id}/submission/{submission_id}/",
            "editable_fields": {  # leaving one as an example
                # 'full_name': {'title': 'Full Name', 'disabled': True},
            },
            "notification_template": notification_template,
            "templates": template_list,
            "submission": submission,
            "case_id": str(case_id),
            "contact": contact,
            "values": values,
        }
        return render(request, template_name, context)

    def post(self, request, case_id, submission_id, *args, **kwargs):
        submission = self._client.get_submission(case_id, submission_id)

        notify_keys = ["full_name", "product", "submission_request_name", "description"]
        notify_data = {key: request.POST.get(key) for key in notify_keys if key in request.POST}
        due_at = get_submission_deadline(submission, settings.FRIENDLY_DATE_FORMAT)
        notify_data["deadline"] = due_at or "No deadline assigned"
        if request.POST.get("multiple"):
            return self.post_multiple(request, case_id, submission, context=notify_data)

        self._client.submission_notify(
            case_id=case_id,
            organisation_id=submission["organisation"]["id"],
            submission_id=submission["id"],
            values=notify_data,
            notice_type=SUBMISSION_NOTICE_TYPE_INVITE,
        )
        return HttpResponse(
            json.dumps(
                {
                    "redirect_url": f"/case/{case_id}/submission/{submission_id}/",
                    "error": None,
                }
            ),
            content_type="application/json",
        )

    def post_multiple(self, request, case_id, submission, context=None):
        """
        Called to handle a notify post to multiple recipents.
        We must clone the submission for each target and send the notification
        """

        case = self._client.get_case(case_id)
        json_data = from_json(submission.get("deficiency_notice_params"))
        send_to = json_data.get("send_to")
        # We need to know which is the last party in the list
        # so we can modify the existing sub rather than clone it.
        party_counter = len(send_to)
        for case_role, participant_list in (
            self._client.get_case_participants(case_id) or {}
        ).items():
            for participant in participant_list.get("parties"):
                if participant.get("id") in send_to:
                    contact = participant.get("primary_contact")
                    party_counter -= 1
                    if contact:  # don't try to send if there is no contact
                        data = {
                            "case_id": case_id,
                            "submission_id": submission["id"],
                            "organisation_id": participant.get("id"),
                            "contact_id": contact.get("id"),
                        }
                        if party_counter:
                            cloned_submission = self._client.clone_submission(**data)
                        else:
                            cloned_submission = self._client.update_submission(**data).get(
                                "submission"
                            )
                        context["full_name"] = contact.get("full_name")
                        self._client.submission_notify(
                            case_id=case_id,
                            organisation_id=participant.get("id"),
                            submission_id=cloned_submission["id"],
                            values=context or {},
                            notice_type=SUBMISSION_NOTICE_TYPE_INVITE,
                        )

        return HttpResponse(
            json.dumps(
                {
                    "alert": f'Sent {len(send_to)} request{"" if len(send_to) < 2 else "s"}',
                    "redirect_url": f'/case/{case_id}/submission/{submission.get("id")}/'
                    if len(send_to) < 2
                    else f"/case/{case_id}/submissions/",
                    "error": None,
                }
            ),
            content_type="application/json",
        )


class OrganisationDetailsView(LoginRequiredMixin, View, TradeRemediesAPIClientMixin):
    def get(self, request, case_id, organisation_id, *args, **kwargs):
        client = self.client(request.user)
        item = request.GET.get("item")
        template = request.GET.get("template")
        result = {}
        case_submissions = client.get_submissions(case_id)
        idx_submissions = deep_index_items_by(case_submissions, "organisation/id")
        org_id = str(organisation_id)
        third_party_contacts = []
        if item == "contacts":
            contacts = client.get_organisation_contacts(org_id, case_id)
            for contact in contacts:
                case = get(contact, "cases/" + str(case_id)) or {}
                contact["primary"] = case.get("primary")
            all_case_invites = client.get_contact_case_invitations(case_id)
            if org_id in idx_submissions:
                org_submission_idx = deep_index_items_by(idx_submissions[org_id], "id")
                third_party_contacts = self.get_third_party_contacts(
                    org_id, org_submission_idx, all_case_invites
                )
            result = {
                "contacts": contacts,
                "pre_release_invitations": client.get_system_boolean("PRE_RELEASE_INVITATIONS"),
                "invites": deep_index_items_by(all_case_invites, "contact/id"),
                "third_party_contacts": third_party_contacts,
                "case_role_id": request.GET.get("caserole"),
            }
        elif item == "submissions":
            result["submissions"] = idx_submissions.get(org_id, [])
        elif item == "details":
            result["party"] = client.get_organisation(organisation_id=organisation_id)
        if template:
            deep_update(
                result,
                {
                    "case_id": case_id,
                    "case": {"id": case_id},
                    "organisation": {"id": org_id},
                },
            )
            return render(request, template, result)
        return HttpResponse(json.dumps({"result": result}), content_type="application/json")

    @staticmethod
    def get_third_party_contacts(organisation_id, submissions, invites):
        """Get third party contacts.

        Given an organisation, its submissions and all invitations for a case,
        build a list of third party invite contacts.

        :param (str) organisation_id: Organisation ID.
        :param (dict) submissions: The organisation's submissions keyed on id.
        :param (list) invites: All invites for a case.
        :returns (list): Contacts arising from 3rd party invite submissions.
        """
        third_party_contacts = []
        for invite in invites:
            if invite["submission"] and invite["submission"]["name"] == "Invite 3rd party":
                submission_id = invite["submission"]["id"]
                full_submission = submissions.get(submission_id)
                if not full_submission:
                    # Submission not at this org
                    continue
                inviting_organisation = full_submission[0]["organisation"]["id"]
                if inviting_organisation == organisation_id:
                    invite_sufficient = full_submission[0]["status"]["sufficient"]
                    invite["contact"]["is_third_party"] = True
                    invite["contact"]["submission_id"] = submission_id
                    invite["contact"]["submission_sufficient"] = invite_sufficient
                    third_party_contacts.append(invite["contact"])
        return third_party_contacts


class CaseOrganisationView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "organisations/organisation_in_case.html"

    def add_page_data(self):
        organisation = self._client.get_organisation(organisation_id=self.organisation_id)
        caserole = None

        case_submissions = self._client.get_submissions_public(self.case_id, self.organisation_id)
        idx_submissions = deep_index_items_by(case_submissions, "organisation/id")

        submissions = idx_submissions.get(str(self.organisation_id), [])
        roi_app_submission = next(
            filter(lambda x: get(x, "type/key") in ["interest", "application"], submissions),
            None,
        )

        cases = self._client.organisation_cases(self.organisation_id)
        user_cases = self._client.organisation_user_cases(self.organisation_id)

        cases_idx = deep_index_items_by_exists(cases, "archived_at")

        for case in cases:
            if get(case, "id") == str(self.case_id):
                caserole = case

        invites = self._client.get_contact_case_invitations(
            self.case_id,
        )
        return {
            "case": self.case,
            "invites": invites,
            "party": organisation,
            "organisation": organisation,
            "cases_idx": cases_idx,
            "submissions": submissions,
            "user_cases": user_cases,
            "roi_app_submission": roi_app_submission,
            "caserole": caserole,
        }


class OrganisationMatchView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/organisation_dedupe.html"

    def add_page_data(self):
        organisation = self._client.get_organisation(
            organisation_id=self.organisation_id, case_id=self.case_id
        )
        org_matches = self._client.get_organisation_matches(self.organisation_id)
        org_matches = decorate_orgs(org_matches, self.organisation_id)
        return {
            "case": self.case,
            "organisation": organisation,
            "org_matches": org_matches,
        }


class FilesView(CaseBaseView):
    """
    View all case documents
    """

    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/files.html"

    def add_page_data(self):
        tab = self.request.GET.get("tab", "respondent")
        sort = self.request.GET.get("sort")
        direction = self.request.GET.get("dir", "asc")
        submission_id = self.request.GET.get("submission_id")
        collapse_identical = self.request.GET.get("collapse_identical", "false") in (
            "true",
            "1",
            "Y",
        )
        tabs = {
            "tabList": [
                {"label": "Respondent", "value": "respondent"},
                {"label": "Investigator", "value": "investigator"},
            ],
            "value": tab,
        }
        case_enums = self._client.get_all_case_enums(direction=DIRECTION_TRA_TO_PUBLIC)
        case_files = self._client.get_case_documents(
            case_id=self.case_id,
            source=tab,
            submission_id=submission_id,
            order_by=sort,
            order_dir=direction,
        )
        submission = None
        if submission_id:
            submission = self._client.get_submission(self.case_id, submission_id)
        return {
            "tabs": tabs,
            "tab": tab,
            "case_enums": case_enums,
            "file_list": case_files,
            "sort": sort,
            "dir": direction,
            "collapse_identical": collapse_identical,
            "submission": submission,
            "pre_document_search": self._client.get_system_boolean("PRE_DOCUMENT_SEARCH"),
        }

    def post(self, request, case_id, *args, **kwargs):
        action = request.POST.get("action")
        name = request.POST.get("name")
        confirm = request.POST.get("confirm") == "true"
        tab = request.POST.get("tab", "respondent")
        document_ids = request.POST.getlist("document_id")
        if document_ids:
            if action == "issue" and confirm:
                submission_type_id = request.POST.get("submission_type_id")
                response = self._client.issue_documents_to_case(
                    case_id=case_id,
                    name=name,
                    document_ids=document_ids,
                    submission_type_id=submission_type_id,
                )
            elif action == "confidential":
                response = self._client.toggle_documents_confidentiality(
                    case_id=case_id, document_ids=document_ids
                )
        return redirect(f"/case/{case_id}/files/?tab={tab}")


class FileBrowseView(View, TradeRemediesAPIClientMixin):
    def get(self, request, case_id, *args, **kwargs):
        _client = self.client(request.user)
        case_files = _client.get_case_documents(case_id=case_id, source="investigator")
        # Add application bundle documents
        case_files.extend(_client.get_system_documents())
        return HttpResponse(json.dumps(case_files), content_type="application/json")


class WorkflowEditor(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    permission_required = ("workflow_editor",)
    template_name = "cases/workflow_editor.html"

    def add_page_data(self):
        case_workflow = self._client.get_case_workflow(self.case_id)
        return {
            "workflow": case_workflow.get("workflow"),
            "state": case_workflow.get("state"),
        }

    def post(self, request, case_id, *args, **kwargs):
        workflow = request.POST.get("workflow")
        self._client.save_case_workflow(case_id, workflow)
        return HttpResponse(json.dumps({"saved": 1}), content_type="application/json")


class ActionsView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/actions.html"

    def add_page_data(self):
        permissions = {}
        for permission_key in self.request.user.permissions:
            permissions[permission_key] = 1
        case_workflow = self._client.get_case_workflow(self.case_id)
        return {
            "workflow": case_workflow.get("workflow"),
            "state": case_workflow.get("state"),
            "permissions": permissions,
        }


class StateView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/action.html"

    def post(self, request, case_id, state_key=None, *args, **kwargs):
        value = request.POST.get(state_key)
        state_map = self._client.set_case_workflow_state(case_id, [state_key], {state_key: value})
        return HttpResponse(
            json.dumps({"workflow_state": state_map}), content_type="application/json"
        )


class ActionView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/action.html"

    def get_state_from_children(self, item):
        any_mode = item.get("required")  # this is a bodge and the logic is reverse
        state = None
        completed = False if any_mode else True
        for child in item.get("children", []):
            value = self.get_value(child.get("key"))
            if value:
                state = state or "in-progress"
            if any_mode:
                if value == "complete":
                    completed = True
            else:
                if value != "complete":
                    completed = False
        return "complete" if state and completed else state

    state_map = {}

    def get_value(self, key):
        return (self.state_map.get(key) or [""])[0]

    def set_value(self, key, value):
        arr = self.state_map.get(key) or [""]
        arr[0] = value
        self.state_map[key] = arr

    def post(self, request, case_id, action_id=None, *args, **kwargs):  # noqa: C901
        values = {}
        node_keys = []
        action_key = request.POST.get("action-key")
        btn_action = request.POST.get("btn_action")
        complete = True
        error = False
        state = ""
        wf = self._client.get_case_workflow(case_id)
        workflow = wf.get("workflow")
        self.state_map = wf.get("state")
        index = key_by(workflow["root"], "key", "children")
        action = index.get(action_key.lower(), {})
        for task in action.get("children", []):
            response_type = task.get("response_type", {}).get("name", "")
            if response_type.lower() not in (
                "notesection",
                "timer",
                "label",
            ):  # notes don't count as in-progress
                task_key = task.get("key")
                old_val = self.get_value(task_key)
                new_val = request.POST.get(task_key)
                if old_val != new_val:
                    values[task_key] = new_val
                    node_keys.append(task_key)

                if not new_val:
                    if task.get("required"):
                        complete = False
                else:
                    if new_val != "na":
                        state = "in-progress"
        if complete:
            state = "complete"
        if (self.get_value(action_key) or "") != state:
            values[action_key] = state
            node_keys.append(action_key)
            self.set_value(action_key, state)

        # ripple the state down the tree
        loc_action = action
        while loc_action.get("parent_key"):
            loc_action = index.get(loc_action.get("parent_key"))
            loc_key = loc_action.get("key")
            loc_state = self.get_state_from_children(loc_action)
            if (self.get_value(loc_key) or "") != loc_state:
                values[loc_key] = loc_state
                node_keys.append(loc_key)
                self.set_value(loc_key, loc_state)

        if any(values):
            self.state_map = self._client.set_case_workflow_state(case_id, node_keys, values)
        if error:
            action_id = action.get("id")
            return redirect(f"/case/{case_id}/action/{action_id}")
        else:
            return HttpResponse(
                json.dumps({"workflow_state": self.state_map}),
                content_type="application/json",
            )


class NavSectionView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/nav_section.html"

    def post(self, request, case_id, *args, **kwargs):
        content_id = kwargs.get("nav_section_id")
        response = self._client.set_case_content(
            case_id, content_id=content_id, content=request.POST
        )
        content_id = response.get("id")
        return redirect(f"/case/{case_id}/section/{content_id}")

    def add_page_data(self):
        return {}


class AuditView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/audit.html"

    def add_page_data(self):
        milestone = self.request.GET.get("milestone", "true") == "true"
        limit = self.request.GET.get("limit")
        audit_data = self._client.get_audit(
            case_id=self.case_id, start=self.start, limit=limit, milestone=milestone
        )
        next_page = prev_page = 0
        if limit and len(audit_data) >= int(limit):
            next_page = int(self.start) + int(limit)
            prev_page = int(self.start) - int(limit)
            if prev_page < 0:
                prev_page = None
        return {
            "milestone": milestone,
            "events": audit_data,
            "limit": limit,
            "start": self.start,
            "next_page": next_page,
            "prev_page": prev_page,
        }


class CaseAuditExport(LoginRequiredMixin, View, TradeRemediesAPIClientMixin):
    groups_required = SECURITY_GROUPS_TRA

    def get(self, request, case_id, *args, **kwargs):
        file = self.client(request.user).get_audit_export(case_id)
        response = HttpResponse(file, content_type="application/vnd.ms-excel")
        response["Content-Disposition"] = "attachment; filename=trade_remedies_export.xls"
        return response


class NoteView(LoginRequiredMixin, View, TradeRemediesAPIClientMixin):
    groups_required = SECURITY_GROUPS_TRA

    def get(
        self,
        request,
        case_id,
        content_type=None,
        model_id=None,
        model_key=None,
        *args,
        **kwargs,
    ):
        notes = self.client(request.user).get_notes(
            case_id, content_type, model_id, model_key=model_key
        )
        return HttpResponse(json.dumps(notes), content_type="application/json")

    def post(self, request, case_id, note_id=None, *args, **kwargs):
        entity_id = request.POST.get("model_id")
        model_key = request.POST.get("model_key")
        content_type = request.POST.get("content_type")
        client = self.client(request.user)
        content = request.POST.get("content")
        if note_id is None:
            result = client.create_note(
                case_id=case_id,
                content_type=content_type,
                model_id=entity_id,
                model_key=model_key,
                note_text=content,
            )
            note_id = result.get("id")
        else:
            delete_list = request.POST.getlist("delete_list")
            if delete_list:
                for document_id in delete_list:
                    deleted = client.delete_note_document(case_id, note_id, document_id)

            conf_list = request.POST.getlist("set_confidential")
            if conf_list:
                for document_id in conf_list:
                    result = client.update_note_document(
                        case_id, note_id, document_id, "confidential"
                    )
            nonconf_list = request.POST.getlist("set_non-confidential")
            if nonconf_list:
                for document_id in nonconf_list:
                    result = client.update_note_document(
                        case_id, note_id, document_id, "non-confidential"
                    )
            result = client.update_note(case_id, note_id, content)

        file_meta = request.POST.getlist("file-meta")
        files = request.FILES.getlist("files")
        for idx, _file in enumerate(files):
            document = {
                "document_name": _file.original_name,
                "name": _file.name,
                "size": _file.file_size,
            }
            result = client.add_note_document(
                case_id=case_id,
                note_id=note_id,
                document=json.dumps(document),
                confidentiality=file_meta[idx],
            )
        redirect_url = request.POST.get("redirect")
        if redirect_url:
            return redirect(redirect_url)
        else:
            # Return note json to be rendered at the client
            return HttpResponse(json.dumps(result), content_type="application/json")


class PublicFileView(CaseBaseView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/public_file.html"

    def add_page_data(self):
        tab = self.request.GET.get("tab", "all")
        tabs = {
            "tabList": [
                {"label": "All", "value": "all"},
                {"label": "Notices", "value": "tra"},
                {"label": "Business", "value": "business"},
                {"label": "Withdrawn", "value": "withdrawn"},
            ],
            "value": tab,
        }

        case_submissions = self._client.get_submissions(self.case_id, show_global=True)
        by_tra = deep_index_items_by_exists(case_submissions, "is_tra")
        tra_by_published = deep_index_items_by_exists(by_tra.get("true"), "issued_at")
        by_published = deep_index_items_by_exists(case_submissions, "issued_at")
        if tab == "all":
            submissions = by_published.get("true")
        if tab == "tra":
            submissions = deep_index_items_by(by_published.get("true"), "is_tra").get("true")
        if tab == "business":
            submissions = deep_index_items_by(by_published.get("true"), "is_tra").get("")
        if tab == "withdrawn":
            submissions = deep_index_items_by(by_published.get("false"), "is_tra").get("true")
        return {
            "tabs": tabs,
            "submissions": submissions,
            "public_base_url": settings.PUBLIC_BASE_URL,
        }


class CaseFormView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/case_form.html"

    def get_context(self, client, case_id=None):
        if case_id:
            case = client.get_case(case_id)
        else:
            case = {
                "new": True,
                "id": "",
                "organisation": {"id": ""},
                "type": {"id": "1"},
            }
        enums = client.get_all_case_enums()
        gov_bodies = client.get_organisations(gov_body=True)
        country_dict = {}
        for country in countries:
            country_dict[country[0]] = country[1]

        context = {
            "body_classes": "full-width",
            "case": case,
            "organisations": gov_bodies,
            "country_dict": country_dict,
            "organisation_name": case.get("organisation", {}).get("name") or "Secretary of State",
            "contact_country": "GB",
            "submission": {"type": {"id": 4}},
            "tra_team_names": [
                settings.ORGANISATION_NAME,
                settings.ORGANISATION_INITIALISM + " Team 1",
                settings.ORGANISATION_INITIALISM + " Team 2",
                settings.ORGANISATION_INITIALISM + " Team 3",
            ],
        }
        context.update(enums)
        # context['countries'] = countries[0]
        return context

    def get(self, request, case_id=None, *args, **kwargs):
        client = self.client(request.user)
        context = self.get_context(client, case_id)
        return render(request, self.template_name, context)

    def post(self, request, case_id=None, *args, **kwargs):
        post_data = {
            "id": case_id,
        }
        non_required_fields = [
            "submission_status_id",
            "case_name",
            "organisation_name",
            "organisation_id",
            # 'organisation_address', 'organisation_post_code', 'companies_house_id',
            # 'contact_name', 'contact_email', 'contact_phone', 'contact_address',
            # 'contact_country',
        ]

        error_lookup = {
            "case_type_id": "Case type",
            "product_name": "Product name",
            "submission_type_id": "Submission type",
            "sector_id": "Product sector",
            "product_description": "Product description",
            "export_country_code": "Export country",
            "hs_code": "Product code",
        }
        required_fields = list(error_lookup.keys())
        list_fields = ["export_country_code", "hs_code"]
        case_fields = required_fields + non_required_fields
        errors = {}
        client = self.client(request.user)
        if request.POST.get("case_type_id") in ALL_REGION_ALLOWED_TYPE_IDS:
            required_fields.remove("export_country_code")
        for field in case_fields:
            post_data[field] = (
                compact_list(request.POST.getlist(field))
                if field in list_fields
                else request.POST.get(field)
            )
        for field in required_fields:
            if field in error_lookup and not post_data.get(field):
                fieldname = error_lookup.get(field)
                errors[field] = f"{fieldname} is required"
        for i, code in enumerate(post_data.get("hs_code")):
            if len(str(code)) not in (6, 7, 8, 9, 10):  # temporary validation
                errors["hs_code"] = "HS codes should be between 6 and 10 digits"
        if not errors:
            post_data["ex_oficio"] = True
            result = client.submit_full_case_data(post_data)
            return redirect("/cases/")
        else:
            context = self.get_context(client, case_id)
            context["errors"] = errors
            context.update(post_data)
            return render(request, self.template_name, context)


class InviteContactView(CaseBaseView):
    """
    Invite a contact to the case
    """

    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/invite.html"
    raise_exception = True

    def get_organisation_admin_user_contact(self, organisation_id):
        contact = None
        organisation = self._client.get_organisation(organisation_id)
        admin_user = [
            user
            for user in organisation.get("users", [])
            if user.get("security_group") == SECURITY_GROUP_ORGANISATION_OWNER
        ]
        if admin_user:
            user = self._client.get_user(admin_user[0]["user_id"])
            contact = user.get("contact")
            contact["organisation"] = organisation
        return contact

    def add_page_data(self):
        contact = None
        organisation = None
        if self.kwargs.get("organisation_id"):
            organisation = self._client.get_organisation(self.kwargs.get("organisation_id"))
        if self.kwargs.get("contact_id"):
            contact = self._client.get_contact(self.kwargs["contact_id"])
            form_url = f"/case/{self.case['id']}/invite/{self.kwargs['contact_id']}/as/{self.kwargs['case_role_id']}/"  # noqa: E501
            if organisation:
                form_url = f"{form_url}for/{organisation['id']}/"
        elif self.kwargs.get("organisation_id"):
            contact = self.get_organisation_admin_user_contact(self.kwargs["organisation_id"])
            form_url = f"/case/{self.case['id']}/invite/organisation/{self.kwargs['organisation_id']}/as/{self.kwargs['case_role_id']}/"  # noqa: E501
        if not organisation:
            organisation = contact["organisation"]
        notification_template = self._client.get_notification_template(
            "NOTIFY_INFORM_INTERESTED_PARTIES"
        )

        deep_update(
            self.case,
            self._client.get_case(
                self.case_id,
                fields=json.dumps(
                    {
                        "Case": {
                            "latest_notice_of_initiation_url": 0,
                            "registration_deadline": 0,
                            "product": 0,
                        }
                    }
                ),
            ),
        )

        values = {
            "full_name": contact["name"],
            "product": get(self.case, "product/name"),
            "case_number": self.case["reference"],
            "case_name": self.case["name"],
            "notice_of_initiation_url": self.case.get("latest_notice_of_initiation_url"),
            "company_name": organisation["name"],
            "deadline": parse_api_datetime(
                get(self.case, "registration_deadline"), settings.FRIENDLY_DATE_FORMAT
            ),
            "footer": self._client.get_system_parameters("NOTIFY_BLOCK_FOOTER")["value"],
            "guidance_url": self._client.get_system_parameters("LINK_HELP_BOX_GUIDANCE")["value"],
            "email": self._client.get_system_parameters("TRADE_REMEDIES_EMAIL")["value"],
            "login_url": f"{settings.PUBLIC_BASE_URL}",
        }
        context = {
            "form_url": form_url,
            "editable_fields": ["full_name", "product"],
            "case": self.case,
            "contact": contact,
            "case_role_id": self.kwargs["case_role_id"],
            "parsed_template": parse_notify_template(notification_template["body"], values),
            "values": values,
            "organisation": organisation,
            "organisation_id": self.kwargs.get("organisation_id"),
        }
        return context

    def post(
        self,
        request,
        contact_id=None,
        case_id=None,
        case_role_id=None,
        organisation_id=None,
        *args,
        **kwargs,
    ):
        notify_keys = ["full_name", "product"]
        notify_data = {key: request.POST.get(key) for key in notify_keys}
        if organisation_id and contact_id:
            notify_data["organisation_id"] = organisation_id
        elif organisation_id and not contact_id:
            contact = self.get_organisation_admin_user_contact(organisation_id)
            contact_id = contact["id"]
        response = self._client.invite_contact(case_id, contact_id, case_role_id, notify_data)
        return HttpResponse(json.dumps(response), content_type="application/json")


class IssueFilesFormView(CaseBaseView):
    """
    Issue files to case
    """

    groups_required = SECURITY_GROUPS_TRA
    template_name = "widgets/issue_files_form.html"

    def add_page_data(self):
        case_enums = self._client.get_all_case_enums()
        return {
            "case_enums": case_enums,
            "case": self.case,
        }


class CaseBundlesView(CaseBaseView):
    """
    Assign documents to the case directly (not via submissions)
    """

    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/case_bundles.html"

    def add_page_data(self):
        list_mode = self.request.GET.get("tab", "live")
        tabs = {
            "value": list_mode,
            "tabList": [
                {"label": "Live", "value": "live", "sr_text": "Show live bundles"},
                {"label": "Draft", "value": "draft", "sr_text": "Show draft bundles"},
            ],
        }
        case_bundles = self._client.get_case_submission_bundles(
            case_id=self.case["id"],
            status=list_mode.upper(),
        )
        return {
            "bundles": case_bundles,
            "error": self.kwargs.get("error"),
            "tabs": tabs,
            "status": list_mode,
        }


@method_decorator(csrf_exempt, name="dispatch")
class CaseBundleView(CaseBaseView):
    """
    View and edit a specific bundle full of documents

    """

    groups_required = SECURITY_GROUPS_TRA
    template_name = "cases/case_bundle_builder.html"

    def add_page_data(self):
        case_enums = self._client.get_all_case_enums()
        bundle = None
        counts = {"virus": 0, "unscanned": 0}
        bundle_id = self.kwargs.get("bundle_id")
        if bundle_id:
            bundle = self._client.get_case_submission_bundles(
                case_id=self.case["id"], bundle_id=self.kwargs.get("bundle_id")
            )
            for document in bundle.get("documents", {}):
                safe = document.get("safe")
                if not safe:
                    if safe is False:
                        counts["virus"] += 1
                    else:
                        counts["unscanned"] += 1
        return {
            "bundle": bundle,
            "submission_types": case_enums["submission_types"],
            "error": self.kwargs.get("error"),
            "counts": counts,
        }

    def post(self, request, case_id, bundle_id=None, *args, **kwargs):  # noqa: C901
        name = request.POST.get("name")
        data = pluck(request.POST, ["name", "description"])
        btn_value = request.POST.get("btn-value")
        if btn_value == "send":
            data["status"] = "LIVE"
        # Upload documents
        if bundle_id:
            meta_raw = request.POST.getlist("meta")
            meta = [json.loads(block) for block in meta_raw]
            file_details = deep_index_items_by(meta, "name")
            for _file in request.FILES.getlist("files"):
                original_file_name = _file.original_name
                details = file_details.get(original_file_name.lower())[0]
                if details:
                    confidential = details.get("confidential")
                    document_type = details.get("submission_document_type")
                    try:
                        document = self._client.upload_document(
                            case_id=str(case_id),
                            data={
                                "bundle_id": bundle_id,
                                "confidential": confidential,
                                "document_name": original_file_name,
                                "file_name": _file.name,
                                "file_size": _file.file_size,
                            },
                        )
                    except Exception as ex:
                        return HttpResponse(
                            json.dumps(
                                {
                                    "redirect_url": f"/case/{case_id}/submission/{submission_id}/edit/?error=up"  # noqa: F821, E501
                                }
                            ),
                            content_type="application/json",
                        )
            # Attach existing documents to this bundle
            case_files = request.POST.getlist("case_files")
            if case_files:
                file_details_by_id = deep_index_items_by(meta, "file/id")
                for case_file_id in case_files:
                    details = (file_details_by_id.get(case_file_id) or [])[0]
                    document = self._client.attach_document(
                        case_id=str(case_id),
                        data={
                            "bundle_id": bundle_id,
                            "submission_document_type": details.get("submission_document_type"),
                        },
                        document_id=case_file_id,
                    )
        else:
            data = pluck(request.POST, ["name", "submission_type_id"])
            data["case_id"] = case_id
        # Anything else to send?
        response = None
        if data:
            response = self._client.set_case_submission_bundle(bundle_id=bundle_id, data=data)
        ret = {"result": "ok", "status": data.get("status")}
        response_id = response and response.get("id")
        if response_id:
            ret["redirect_url"] = f"/case/{case_id}/bundle/{response_id}/"
        return HttpResponse(json.dumps(ret), content_type="application/json")

    def delete(self, request, case_id, document_id, *args, **kwargs):
        response = self._client.delete_case_submission_bundle(case_id, document_id)
        return redirect(f"/case/{case_id}/documents/")


class SubmissionInviteNotifyView(CaseBaseView):
    """
    Notify an invitee about an invitation to case.
    """

    groups_required = SECURITY_GROUPS_TRA
    raise_exception = True
    template_name = "cases/invite.html"

    def add_page_data(self):
        """Add page data.

        CaseBaseView override.
        """
        case_id = self.kwargs.get("case_id")
        submission_id = self.kwargs.get("submission_id")
        contact_id = self.kwargs.get("contact_id")
        case = self._client.get_case(case_id)
        submission = self._client.get_submission(case_id, submission_id)
        inviting_organisation = submission["organisation"]
        invited_contact = self._client.get_contact(contact_id)
        inviting_contact = submission.get("contact") or {}
        notification_template = self._client.get_notification_template("NOTIFY_THIRD_PARTY_INVITE")
        form_url = f"/case/{case_id}/submission/{submission_id}/invite/{contact_id}/notify/"

        values = {
            "full_name": invited_contact["name"],
            "case_name": case["name"],
            "invited_by_organisation": inviting_organisation["name"],
            "invited_by_name": inviting_contact["name"],
            "notice_of_initiation_url": self.case.get("latest_notice_of_initiation_url"),
            "deadline": parse_api_datetime(
                get(self.case, "registration_deadline"), settings.FRIENDLY_DATE_FORMAT
            ),
            "footer": self._client.get_system_parameters("NOTIFY_BLOCK_FOOTER")["value"],
            "email": self._client.get_system_parameters("TRADE_REMEDIES_EMAIL")["value"],
        }

        context = {
            "form_url": form_url,
            "notification_template": notification_template,
            "submission": submission,
            "case": case,
            "contact": invited_contact,
            "parsed_template": parse_notify_template(notification_template["body"], values),
            "values": values,
        }
        return context

    def post(self, request, case_id, submission_id, contact_id, *args, **kwargs):
        notify_data = {
            "case_id": case_id,
            "submission_id": submission_id,
            "contact_id": contact_id,
        }
        response = self._client.action_third_party_invite(
            case_id=case_id,
            submission_id=submission_id,
            contact_id=contact_id,
            params=notify_data,
        )
        return HttpResponse(json.dumps(response), content_type="application/json")


class UpdateParentView(CaseBaseView):
    template_name = "cases/update_parent.html"

    linked_case_confirm_key = "LINKED_CASE_CONFIRM"
    cases_fields = json.dumps(
        {
            "Case": {
                "name": 0,
                "id": 0,
                "reference": 0,
            }
        }
    )

    case_fields = json.dumps(
        {"Case": {"parent": {"id": 0}, "workflow_state": {linked_case_confirm_key: 0}}}
    )

    def add_page_data(self):
        cases = self._client.get_cases(archived=True, all_cases=False, fields=self.cases_fields)
        case = self._client.get_case(self.case_id, fields=self.case_fields)
        return {"case": case, "cases": cases}

    def post(self, request, case_id, *args, **kwargs):
        link_confirm = request.POST.get("link_confirm")
        parent_id = request.POST.get("parent_id")
        _client = self.client(request.user)
        case = _client.get_case(case_id, fields=self.case_fields)
        if get(case, "parent/id") != parent_id:
            _client.set_case_data(case_id, {"parent_id": parent_id})
        if (get(case, f"workflow_state/{self.linked_case_confirm_key}") or [0])[0] != link_confirm:
            _client.set_case_workflow_state(
                case_id, values={f"{self.linked_case_confirm_key}": link_confirm}
            )
        return HttpResponse(
            json.dumps({"parent_id": parent_id, "link_confirm": link_confirm}),
            content_type="application/json",
        )


class NoticesView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = SECURITY_GROUPS_TRA_ADMINS
    template_name = "cases/notices.html"

    def get(self, request):
        client = self.client(request.user)
        notices = client.get_notices()
        return render(
            request,
            self.template_name,
            {
                "body_classes": "full-width",
                "notices": notices,
            },
        )


class NoticeView(LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    groups_required = SECURITY_GROUPS_TRA_ADMINS
    template_name = "cases/notice.html"
    cases_fields = json.dumps({"Case": {"name": 0, "id": 0, "reference": 0}})

    def get(self, request, notice_id=None):
        client = self.client(request.user)
        enums = client.get_all_case_enums()
        case_types = enums.get("case_types", [])
        cases = client.get_cases(archived=True, all_cases=False, fields=self.cases_fields)
        notice = {}
        if notice_id:
            notice = client.get_notice(notice_id)
        return render(
            request,
            self.template_name,
            {
                "body_classes": "full-width",
                "notice": notice,
                "cases": cases,
                "case_types": case_types,
            },
        )

    def post(self, request, notice_id=None):
        client = self.client(request.user)
        notice = client.create_update_notice(
            name=request.POST.get("name"),
            reference=request.POST.get("reference"),
            terminated_at=request.POST.get("terminated_at"),
            published_at=request.POST.get("published_at"),
            case_type=request.POST.get("case_type_id"),
            review_case=request.POST.get("review_case_id"),
            notice_id=notice_id,
        )
        return redirect("/cases/notices/")


class DocumentSearchView(CaseBaseView):
    template_name = "documents/documents.html"

    def add_page_data(self):
        query = self.request.GET.get("query")
        conf_status = self.request.GET.get("confidential_status")
        user_type = self.request.GET.get("user_type")
        response = self._client.search_documents(
            case_id=self.case_id,
            query=query,
            confidential_status=conf_status,
            user_type=user_type,
        )
        # results = response.get('response', {}).pop('results', [])
        return {
            "body_classes": "full-width",
            "documents": response.pop("results", []),
            "query": query,
            "conf_status": conf_status,
            **response,
        }


class CaseTeamJsonView(LoginRequiredMixin, View, TradeRemediesAPIClientMixin):
    def get(self, request, case_id, **kwargs):
        team = self.client(request.user).get_case_team_members(case_id)
        return HttpResponse(json.dumps(team), content_type="application/json")
