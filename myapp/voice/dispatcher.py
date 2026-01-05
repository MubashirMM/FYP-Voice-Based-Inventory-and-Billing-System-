# voice/dispatcher.py
async def dispatch_action(user_id: int, entities: dict):
    if entities["intent"] == "add_udhar":
        # call your existing function
        return {
            "message": "چینی دس کلو اُدھار میں شامل کر دی گئی"
        }

    return {
        "message": "درخواست سمجھ میں نہیں آئی"
    }
