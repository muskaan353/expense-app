from apps.balances.services import calculate_group_balances


def answer_balance_question(*, group, user, question):
    result = calculate_group_balances(group=group)
    normalized_question = question.casefold()
    member = next(
        (item for item in result["members"] if item["user_id"] == user.id),
        None,
    )

    if any(word in normalized_question for word in ("why", "breakdown", "explain")):
        if member is None:
            answer = "You have no ledger entries in this group."
            data = {"balance": "0.00", "entries": []}
            citations = []
        else:
            answer = (
                f"Your net balance is {member['balance']} {result['currency']}. "
                "The response includes every expense and settlement contributing to it."
            )
            data = member
            citations = [
                {"kind": entry["kind"], "reference_id": entry["reference_id"]}
                for entry in member["entries"]
            ]
    elif any(word in normalized_question for word in ("settle", "pay", "owe")):
        relevant = [
            debt
            for debt in result["suggested_settlements"]
            if user.id in (debt["payer_id"], debt["payee_id"])
        ]
        answer = (
            "These payments settle the group using the current verified ledger."
            if relevant
            else "You do not currently need to send or receive a payment."
        )
        data = {"suggested_settlements": relevant, "currency": result["currency"]}
        citations = []
    else:
        answer = (
            "Here is the current group balance summary. Ask why a balance exists "
            "or who should pay whom for a narrower explanation."
        )
        data = result
        citations = []

    return {
        "answer": answer,
        "data": data,
        "citations": citations,
        "generated_from": "deterministic_ledger",
    }
