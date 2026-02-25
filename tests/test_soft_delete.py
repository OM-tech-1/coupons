"""
Test soft delete logic for coupons and packages.

Tests verify that:
1. Items with references (orders/carts) are soft deleted (is_active=False)
2. Items without references are hard deleted (removed from DB)
3. Users can still see their owned coupons even if soft deleted
4. Public listings don't show soft deleted items
5. Admins can see soft deleted items with proper filters
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.models.coupon import Coupon
from app.models.package import Package
from app.models.order import Order, OrderItem
from app.models.cart import CartItem
from app.models.user_coupon import UserCoupon
from app.models.user import User
from app.services.coupon_service import CouponService
from app.services.package_service import PackageService
from app.utils.security import get_password_hash


# Fixtures
@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = User(
        phone_number="+1234567890",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        role="USER",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_coupon(db):
    """Create a test coupon"""
    coupon = Coupon(
        code=f"TEST{uuid4().hex[:8].upper()}",
        title="Test Coupon",
        discount_type="percentage",
        discount_amount=10.0,
        price=5.0,
        is_active=True
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@pytest.fixture
def test_package(db):
    """Create a test package"""
    package = Package(
        name="Test Package",
        slug=f"test-package-{uuid4().hex[:8]}",
        description="Test package description",
        is_active=True
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


class TestCouponSoftDelete:
    """Test soft delete logic for coupons"""
    
    def test_delete_coupon_with_order_soft_deletes(self, db, test_user, test_coupon):
        """Coupon with order should be soft deleted (is_active=False)"""
        # Create an order with this coupon
        order = Order(
            user_id=test_user.id,
            total_amount=10.0,
            currency="USD",
            status="paid"
        )
        db.add(order)
        db.flush()
        
        order_item = OrderItem(
            order_id=order.id,
            coupon_id=test_coupon.id,
            quantity=1,
            price=10.0
        )
        db.add(order_item)
        db.commit()
        
        # Try to delete the coupon
        result = CouponService.delete(db, test_coupon.id)
        
        # Should succeed
        assert result is True
        
        # Coupon should still exist but be inactive
        coupon = db.query(Coupon).filter(Coupon.id == test_coupon.id).first()
        assert coupon is not None
        assert coupon.is_active is False
        assert coupon.is_featured is False
    
    def test_delete_coupon_in_cart_soft_deletes(self, db, test_user, test_coupon):
        """Coupon in cart should be soft deleted"""
        # Add coupon to cart
        cart_item = CartItem(
            user_id=test_user.id,
            coupon_id=test_coupon.id,
            quantity=1
        )
        db.add(cart_item)
        db.commit()
        
        # Try to delete the coupon
        result = CouponService.delete(db, test_coupon.id)
        
        # Should succeed
        assert result is True
        
        # Coupon should still exist but be inactive
        coupon = db.query(Coupon).filter(Coupon.id == test_coupon.id).first()
        assert coupon is not None
        assert coupon.is_active is False
    
    def test_delete_unused_coupon_hard_deletes(self, db, test_coupon):
        """Coupon with no references should be hard deleted"""
        coupon_id = test_coupon.id
        
        # Delete the coupon (no orders, no cart items)
        result = CouponService.delete(db, coupon_id)
        
        # Should succeed
        assert result is True
        
        # Coupon should be completely removed
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        assert coupon is None
    
    def test_soft_deleted_coupon_not_in_public_list(self, db, test_coupon):
        """Soft deleted coupons should not appear in public listing"""
        # Soft delete the coupon
        test_coupon.is_active = False
        db.commit()
        
        # Get coupons with active_only=True (default)
        coupons = CouponService.get_all(db, active_only=True)
        
        # Soft deleted coupon should not be in the list
        coupon_ids = [c.id for c in coupons]
        assert test_coupon.id not in coupon_ids
    
    def test_soft_deleted_coupon_visible_to_admin(self, db, test_coupon):
        """Admins should see soft deleted coupons with active_only=False"""
        # Soft delete the coupon
        test_coupon.is_active = False
        db.commit()
        
        # Get coupons with active_only=False
        coupons = CouponService.get_all(db, active_only=False)
        
        # Soft deleted coupon should be in the list
        coupon_ids = [c.id for c in coupons]
        assert test_coupon.id in coupon_ids
    
    def test_user_wallet_shows_soft_deleted_coupons(self, db, test_user, test_coupon):
        """Users should see soft deleted coupons they own in their wallet"""
        # User owns the coupon
        user_coupon = UserCoupon(
            user_id=test_user.id,
            coupon_id=test_coupon.id
        )
        db.add(user_coupon)
        db.commit()
        
        # Soft delete the coupon
        test_coupon.is_active = False
        db.commit()
        
        # Get user's wallet
        from app.services.user_coupon_service import UserCouponService
        wallet_coupons = UserCouponService.get_wallet_coupons(db, test_user.id)
        
        # User should still see the coupon
        coupon_ids = [c['coupon_id'] for c in wallet_coupons]
        assert test_coupon.id in coupon_ids
        
        # Check that is_active is False in the response
        user_coupon_data = next(c for c in wallet_coupons if c['coupon_id'] == test_coupon.id)
        assert user_coupon_data['is_active'] is False


class TestPackageSoftDelete:
    """Test soft delete logic for packages"""
    
    def test_delete_package_with_order_soft_deletes(self, db, test_user, test_package):
        """Package with order should be soft deleted"""
        # Create an order with this package
        order = Order(
            user_id=test_user.id,
            total_amount=20.0,
            currency="USD",
            status="paid"
        )
        db.add(order)
        db.flush()
        
        order_item = OrderItem(
            order_id=order.id,
            package_id=test_package.id,
            quantity=1,
            price=20.0
        )
        db.add(order_item)
        db.commit()
        
        # Try to delete the package
        result = PackageService.delete(db, test_package.id)
        
        # Should succeed
        assert result is True
        
        # Package should still exist but be inactive
        package = db.query(Package).filter(Package.id == test_package.id).first()
        assert package is not None
        assert package.is_active is False
        assert package.is_featured is False
    
    def test_delete_unused_package_hard_deletes(self, db, test_package):
        """Package with no orders should be hard deleted"""
        package_id = test_package.id
        
        # Delete the package (no orders)
        result = PackageService.delete(db, package_id)
        
        # Should succeed
        assert result is True
        
        # Package should be completely removed
        package = db.query(Package).filter(Package.id == package_id).first()
        assert package is None
    
    def test_soft_deleted_package_not_in_public_list(self, db, test_package):
        """Soft deleted packages should not appear in public listing"""
        # Soft delete the package
        test_package.is_active = False
        db.commit()
        
        # Get packages with is_active=True (default)
        packages = PackageService.get_all(db, is_active=True)
        
        # Soft deleted package should not be in the list
        package_ids = [p['id'] for p in packages]
        assert test_package.id not in package_ids
    
    def test_soft_deleted_package_visible_to_admin(self, db, test_package):
        """Admins should see soft deleted packages with is_active=False"""
        # Soft delete the package
        test_package.is_active = False
        db.commit()
        
        # Get packages with is_active=False
        packages = PackageService.get_all(db, is_active=False)
        
        # Soft deleted package should be in the list
        package_ids = [p['id'] for p in packages]
        assert test_package.id in package_ids


class TestDeleteWithMultipleReferences:
    """Test deletion when items have multiple references"""
    
    def test_coupon_in_cart_and_order_soft_deletes(self, db, test_user, test_coupon):
        """Coupon in both cart and order should be soft deleted"""
        # Add to cart
        cart_item = CartItem(
            user_id=test_user.id,
            coupon_id=test_coupon.id,
            quantity=1
        )
        db.add(cart_item)
        
        # Add to order
        order = Order(
            user_id=test_user.id,
            total_amount=10.0,
            currency="USD",
            status="paid"
        )
        db.add(order)
        db.flush()
        
        order_item = OrderItem(
            order_id=order.id,
            coupon_id=test_coupon.id,
            quantity=1,
            price=10.0
        )
        db.add(order_item)
        db.commit()
        
        # Delete should soft delete
        result = CouponService.delete(db, test_coupon.id)
        assert result is True
        
        # Coupon should still exist but be inactive
        coupon = db.query(Coupon).filter(Coupon.id == test_coupon.id).first()
        assert coupon is not None
        assert coupon.is_active is False
        
        # Cart and order references should still work
        cart = db.query(CartItem).filter(CartItem.coupon_id == test_coupon.id).first()
        assert cart is not None
        
        order_item = db.query(OrderItem).filter(OrderItem.coupon_id == test_coupon.id).first()
        assert order_item is not None


class TestRestoreSoftDeletedItems:
    """Test restoring soft deleted items"""
    
    def test_restore_soft_deleted_coupon(self, db, test_coupon):
        """Soft deleted coupon can be restored by setting is_active=True"""
        # Soft delete
        test_coupon.is_active = False
        db.commit()
        
        # Verify it's not in public list
        coupons = CouponService.get_all(db, active_only=True)
        assert test_coupon.id not in [c.id for c in coupons]
        
        # Restore
        from app.schemas.coupon import CouponUpdate
        update_data = CouponUpdate(is_active=True)
        restored = CouponService.update(db, test_coupon.id, update_data)
        
        # Should be active again
        assert restored.is_active is True
        
        # Should appear in public list
        coupons = CouponService.get_all(db, active_only=True)
        assert test_coupon.id in [c.id for c in coupons]
    
    def test_restore_soft_deleted_package(self, db, test_package):
        """Soft deleted package can be restored"""
        # Soft delete
        test_package.is_active = False
        db.commit()
        
        # Restore
        from app.schemas.package import PackageUpdate
        update_data = PackageUpdate(is_active=True)
        restored = PackageService.update(db, test_package.id, update_data)
        
        # Should be active again
        assert restored is not None
        
        # Verify in database
        package = db.query(Package).filter(Package.id == test_package.id).first()
        assert package.is_active is True

