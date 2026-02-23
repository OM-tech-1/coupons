import json

with open("coupon_app_collection.json", "r") as f:
    data = json.load(f)

for folder in data.get("item", []):
    if folder.get("name") == "Cart":
        for req_item in folder.get("item", []):
            if req_item.get("name") == "Remove from Cart":
                # Update the URL
                req = req_item.get("request", {})
                url = req.get("url", {})
                
                # Update raw URL
                raw = url.get("raw", "")
                url["raw"] = raw.replace("{{base_url}}/cart/{{coupon_id}}", "{{base_url}}/cart/{{item_id}}")
                
                # Update path
                path = url.get("path", [])
                if path and len(path) > 1 and path[-1] == "{{coupon_id}}":
                    path[-1] = "{{item_id}}"
                    
                # Update variables
                variables = url.get("variable", [])
                for var in variables:
                    if var.get("key") == "coupon_id":
                        var["key"] = "item_id"
                        var["value"] = "{{item_id}}"
                        var["description"] = "ID of the coupon or package to remove"

with open("coupon_app_collection.json", "w") as f:
    json.dump(data, f, indent=4)
print("Cart Updated")
