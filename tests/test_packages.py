"""Tests for the Package CRUD endpoints."""

class TestPackageCRUD:

    def test_create_package(self, client, admin_user, sample_coupon, sample_category):
        resp = client.post("/packages/", json={
            "name": "Holiday Bundle",
            "slug": "holiday-bundle",
            "description": "A holiday pack",
            "category_id": sample_category["id"],
            "coupon_ids": [sample_coupon["id"]],
        }, headers=admin_user["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Holiday Bundle"
        assert data["category"]["slug"] == "electronics"
        assert len(data["coupons"]) == 1
        assert data["coupons"][0]["id"] == sample_coupon["id"]

    def test_create_package_non_admin(self, client, regular_user):
        resp = client.post("/packages/", json={
            "name": "Hack Pack",
            "slug": "hack-pack",
        }, headers=regular_user["headers"])
        assert resp.status_code == 403

    def test_list_packages(self, client, admin_user):
        client.post("/packages/", json={
            "name": "Pack 1", "slug": "pack-1",
        }, headers=admin_user["headers"])
        client.post("/packages/", json={
            "name": "Pack 2", "slug": "pack-2",
        }, headers=admin_user["headers"])
        resp = client.get("/packages/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_package_by_id(self, client, admin_user):
        create = client.post("/packages/", json={
            "name": "ID Lookup", "slug": "id-lookup",
        }, headers=admin_user["headers"])
        pkg_id = create.json()["id"]
        resp = client.get(f"/packages/{pkg_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "ID Lookup"

    def test_get_package_not_found(self, client):
        import uuid
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/packages/{fake_id}")
        assert resp.status_code == 404

    def test_update_package(self, client, admin_user):
        create = client.post("/packages/", json={
            "name": "Old Name", "slug": "old-name",
        }, headers=admin_user["headers"])
        pkg_id = create.json()["id"]
        resp = client.put(f"/packages/{pkg_id}", json={
            "name": "New Name",
        }, headers=admin_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_delete_package(self, client, admin_user):
        create = client.post("/packages/", json={
            "name": "To Delete", "slug": "to-delete",
        }, headers=admin_user["headers"])
        pkg_id = create.json()["id"]
        resp = client.delete(f"/packages/{pkg_id}", headers=admin_user["headers"])
        assert resp.status_code == 204
        assert client.get(f"/packages/{pkg_id}").status_code == 404

    def test_add_coupons_to_package(self, client, admin_user, sample_coupon):
        create = client.post("/packages/", json={
            "name": "Addon Pack", "slug": "addon-pack",
        }, headers=admin_user["headers"])
        pkg_id = create.json()["id"]
        resp = client.post(
            f"/packages/{pkg_id}/coupons",
            json=[sample_coupon["id"]],
            headers=admin_user["headers"],
        )
        assert resp.status_code == 200
        assert len(resp.json()["coupons"]) == 1

    def test_remove_coupon_from_package(self, client, admin_user, sample_coupon):
        create = client.post("/packages/", json={
            "name": "Removal Pack", "slug": "removal-pack",
            "coupon_ids": [sample_coupon["id"]],
        }, headers=admin_user["headers"])
        pkg_id = create.json()["id"]
        resp = client.delete(
            f"/packages/{pkg_id}/coupons/{sample_coupon['id']}",
            headers=admin_user["headers"],
        )
        assert resp.status_code == 200
        assert len(resp.json()["coupons"]) == 0

    def test_package_coupon_excluded_from_coupon_listing(self, client, admin_user, sample_coupon):
        """Coupons added to a package should NOT appear in /coupons/"""
        client.post("/packages/", json={
            "name": "Visibility Pack", "slug": "visibility-pack",
            "coupon_ids": [sample_coupon["id"]],
        }, headers=admin_user["headers"])
        resp = client.get("/coupons/")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert sample_coupon["id"] not in ids

    def test_get_package_coupons(self, client, admin_user, sample_coupon):
        create = client.post("/packages/", json={
            "name": "Coupon List Pack", "slug": "coupon-list-pack",
            "coupon_ids": [sample_coupon["id"]],
        }, headers=admin_user["headers"])
        pkg_id = create.json()["id"]
        resp = client.get(f"/packages/{pkg_id}/coupons")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_create_package_with_brand_and_discount(self, client, admin_user):
        resp = client.post("/packages/", json={
            "name": "Branded Bundle",
            "slug": "branded-bundle",
            "brand": "Noon",
            "discount": 15.0,
        }, headers=admin_user["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["brand"] == "Noon"
        assert data["discount"] == 15.0

    def test_package_total_price(self, client, admin_user):
        """total_price should be the sum of coupon prices per currency."""
        c1 = client.post("/coupons/", json={
            "code": "TP1", "redeem_code": "R-TP1",
            "title": "Coupon TP1", "discount_type": "percentage",
            "discount_amount": 5.0, "price": 10.0,
            "pricing": {"INR": {"price": 100.0}, "AED": {"price": 20.0}},
        }, headers=admin_user["headers"]).json()
        c2 = client.post("/coupons/", json={
            "code": "TP2", "redeem_code": "R-TP2",
            "title": "Coupon TP2", "discount_type": "percentage",
            "discount_amount": 3.0, "price": 5.0,
            "pricing": {"INR": {"price": 50.0}, "AED": {"price": 10.0}},
        }, headers=admin_user["headers"]).json()
        pkg = client.post("/packages/", json={
            "name": "Total Price Pack", "slug": "total-price-pack",
            "coupon_ids": [c1["id"], c2["id"]],
        }, headers=admin_user["headers"]).json()
        assert pkg["total_price"]["INR"] == 150.0
        assert pkg["total_price"]["AED"] == 30.0

    def test_package_coupons_include_pricing(self, client, admin_user):
        """Coupons in the package response should include pricing info."""
        c = client.post("/coupons/", json={
            "code": "PRC1", "redeem_code": "R-PRC1",
            "title": "Priced Coupon", "discount_type": "percentage",
            "discount_amount": 5.0, "price": 8.0,
            "pricing": {"INR": {"price": 80.0, "discount_amount": 5.0}},
        }, headers=admin_user["headers"]).json()
        pkg = client.post("/packages/", json={
            "name": "Pricing Pack", "slug": "pricing-pack",
            "coupon_ids": [c["id"]],
        }, headers=admin_user["headers"]).json()
        coupon_in_pkg = pkg["coupons"][0]
        assert "pricing" in coupon_in_pkg
        assert coupon_in_pkg["pricing"]["INR"]["price"] == 80.0
        assert coupon_in_pkg["price"] == 8.0

    def test_list_packages_active_only_by_default(self, client, admin_user):
        """GET /packages/ should only return active packages by default."""
        client.post("/packages/", json={
            "name": "Active Pack", "slug": "active-pack", "is_active": True,
        }, headers=admin_user["headers"])
        client.post("/packages/", json={
            "name": "Inactive Pack", "slug": "inactive-pack", "is_active": False,
        }, headers=admin_user["headers"])
        resp = client.get("/packages/")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "Active Pack" in names
        assert "Inactive Pack" not in names

    def test_filter_by_highest_saving(self, client, admin_user):
        """Filter by highest_saving should order by discount DESC."""
        client.post("/packages/", json={
            "name": "Low Save", "slug": "low-save", "discount": 5.0,
        }, headers=admin_user["headers"])
        client.post("/packages/", json={
            "name": "High Save", "slug": "high-save", "discount": 50.0,
        }, headers=admin_user["headers"])
        resp = client.get("/packages/?filter=highest_saving")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        assert data[0]["name"] == "High Save"

    def test_filter_by_avg_rating(self, client, admin_user):
        """Filter by avg_rating should order by avg_rating DESC."""
        client.post("/packages/", json={
            "name": "Low Rated", "slug": "low-rated", "avg_rating": 1.0,
        }, headers=admin_user["headers"])
        client.post("/packages/", json={
            "name": "Top Rated", "slug": "top-rated", "avg_rating": 4.8,
        }, headers=admin_user["headers"])
        resp = client.get("/packages/?filter=avg_rating")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["name"] == "Top Rated"

    def test_filter_by_bundle_sold(self, client, admin_user):
        """Filter by bundle_sold should order by total_sold DESC."""
        client.post("/packages/", json={
            "name": "Few Sold", "slug": "few-sold", "total_sold": 10,
        }, headers=admin_user["headers"])
        client.post("/packages/", json={
            "name": "Best Seller", "slug": "best-seller", "total_sold": 500,
        }, headers=admin_user["headers"])
        resp = client.get("/packages/?filter=bundle_sold")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["name"] == "Best Seller"

    def test_package_response_includes_stats(self, client, admin_user):
        """Package response should include avg_rating, total_sold, max_saving."""
        resp = client.post("/packages/", json={
            "name": "Stats Pack", "slug": "stats-pack",
            "discount": 20.0, "avg_rating": 3.5, "total_sold": 100,
        }, headers=admin_user["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["avg_rating"] == 3.5
        assert data["total_sold"] == 100
        assert data["max_saving"] == 20.0

    def test_add_package_to_cart(self, client, admin_user, regular_user):
        """POST /cart/add with package_id should add a package to cart."""
        pkg = client.post("/packages/", json={
            "name": "Cart Pack", "slug": "cart-pack",
        }, headers=admin_user["headers"]).json()
        resp = client.post("/cart/add", json={
            "package_id": pkg["id"], "quantity": 1,
        }, headers=regular_user["headers"])
        assert resp.status_code == 201
        assert resp.json()["message"] == "Added to cart"
        assert resp.json()["package_id"] == pkg["id"]

    def test_remove_package_from_cart(self, client, admin_user, regular_user):
        """DELETE /cart/{item_id} should remove a package from the cart."""
        pkg = client.post("/packages/", json={
            "name": "Remove Pack", "slug": "remove-pack",
        }, headers=admin_user["headers"]).json()
        
        # Add to cart
        client.post("/cart/add", json={
            "package_id": pkg["id"], "quantity": 1,
        }, headers=regular_user["headers"])
        
        # Verify in cart and get cart item ID
        cart_resp = client.get("/cart/", headers=regular_user["headers"])
        assert len(cart_resp.json()["items"]) == 1
        cart_item_id = cart_resp.json()["items"][0]["id"]
        
        # Remove from cart using cart item ID (not package ID)
        del_resp = client.delete(f"/cart/{cart_item_id}", headers=regular_user["headers"])
        assert del_resp.status_code == 204
        
        # Verify empty
        cart_resp2 = client.get("/cart/", headers=regular_user["headers"])
        assert len(cart_resp2.json()["items"]) == 0

