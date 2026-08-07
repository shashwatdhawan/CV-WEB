from backend.services.orders import serialize_order


def build_purchase_ticket_payload(order) -> dict:
    data = serialize_order(order)
    return {
        "order_id": data["orderId"],
        "customer_mention": f"<@{data['discordId']}>",
        "discord_username": data["discordUsername"],
        "discord_id": data["discordId"],
        "minecraft_username": data["minecraftIgn"],
        "minecraft_type": data["minecraftAccountType"],
        "account_type": data["minecraftAccountType"],
        "premium": data["minecraftPremium"],
        "products": [
            {
                "id": item["productId"],
                "name": item["name"],
                "quantity": item["quantity"],
                "price": item["unitPrice"],
                "line_total": item["lineTotal"],
                "category": item["category"],
            }
            for item in data["items"]
        ],
        "coupon": data["coupon"],
        "discount": data["discount"],
        "subtotal": data["subtotal"],
        "total": data["finalTotal"],
        "final_total": data["finalTotal"],
        "created_at": data["createdAt"],
        "created_time": data["createdAt"],
        "status": data["status"],
    }
