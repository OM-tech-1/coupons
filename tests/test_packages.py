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
