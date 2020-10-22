from core.utils import get


def decorate_orgs(org_list, representing_org_id, exclude_case_id=None):
    # If exclude_case_id is provided, references to that case are excluded
    verified_cases = {}

    def collate_cases(user_cases):
        # flatten user_cases by org and case.
        # so <org_id>/<case_id>/ contains {case:<case>,users:[<user>,..]}

        nonlocal exclude_case_id

        out = {}
        for user_case in user_cases or []:
            case_id = get(user_case, "case/id")
            org_id = get(user_case, "organisation/id")
            if str(case_id) != str(exclude_case_id):
                case_org_id = f"{case_id}:{org_id}"
                out.setdefault(
                    case_org_id,
                    {
                        "case": get(user_case, "case"),
                        "caserole": get(user_case, "caserole"),
                        "organisation": get(user_case, "organisation"),
                        "usercases": [],
                    },
                )
                if get(user_case, "caserole/validated_at"):
                    verified_cases[case_org_id] = out[case_org_id]
                out[case_org_id]["usercases"].append(get(user_case, "usercase"))
        return list(out.values())

    for org in org_list:
        org["collated_cases"] = collate_cases(org.get("cases"))
        org["collated_indirect_cases"] = collate_cases(org.get("indirect_cases"))

        usercases = org.get("collated_indirect_cases")
        if usercases:
            org["cases_for_org"] = list(
                [
                    case
                    for case in usercases
                    if get(case, "organisation/id") == representing_org_id
                ]
            )
        org["verified_usercases"] = list(verified_cases.values())
        org["verified_usercases"].sort(
            key=lambda uc: get(uc, "caserole/validated_at", ""), reverse=True
        )

    return org_list
