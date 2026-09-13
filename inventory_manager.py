import sqlite3
from typing import List, Optional, Tuple


class InventoryManager:
    def __init__(self, db_name: str = "inventory.db"):
        self.db_name = db_name
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_name)

    def _init_db(self):
        """Khởi tạo bảng cơ sở dữ liệu nếu chưa tồn tại."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0),
                    price REAL NOT NULL CHECK(price >= 0)
                )
                """
            )
            conn.commit()

    def add_product(self, sku: str, name: str, quantity: int, price: float) -> bool:
        """Thêm sản phẩm mới vào kho."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO products (sku, name, quantity, price) VALUES (?, ?, ?, ?)",
                    (sku.strip().upper(), name.strip(), quantity, price),
                )
                conn.commit()
                print(f"-> Đã thêm sản phẩm: {name} (Mã: {sku.upper()})")
                return True
        except sqlite3.IntegrityError:
            print(f"-> Lỗi: Mã sản phẩm '{sku.upper()}' đã tồn tại hoặc số lượng/giá không hợp lệ.")
            return False

    def list_products(self) -> List[Tuple]:
        """Lấy danh sách tất cả sản phẩm."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, sku, name, quantity, price FROM products ORDER BY id ASC")
            return cursor.fetchall()

    def update_stock(self, sku: str, amount: int) -> bool:
        """Nhập thêm (amount > 0) hoặc Xuất kho (amount < 0)."""
        sku = sku.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM products WHERE sku = ?", (sku,))
            row = cursor.fetchone()

            if not row:
                print(f"-> Không tìm thấy sản phẩm có mã '{sku}'.")
                return False

            current_qty = row[0]
            new_qty = current_qty + amount

            if new_qty < 0:
                print(f"-> Lỗi xuất kho: Số lượng tồn kho chỉ còn {current_qty}, không đủ để xuất {abs(amount)}.")
                return False

            cursor.execute("UPDATE products SET quantity = ? WHERE sku = ?", (new_qty, sku))
            conn.commit()
            action = "Nhập thêm" if amount > 0 else "Xuất"
            print(f"-> {action} thành công. Tồn kho mới của {sku}: {new_qty}")
            return True

    def search_product(self, keyword: str) -> List[Tuple]:
        """Tìm kiếm theo mã SKU hoặc tên sản phẩm."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{keyword.strip()}%"
            cursor.execute(
                "SELECT id, sku, name, quantity, price FROM products WHERE sku LIKE ? OR name LIKE ?",
                (pattern, pattern),
            )
            return cursor.fetchall()

    def delete_product(self, sku: str) -> bool:
        """Xóa sản phẩm theo mã SKU."""
        sku = sku.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE sku = ?", (sku,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"-> Đã xóa sản phẩm mã '{sku}'.")
                return True
            else:
                print(f"-> Không tìm thấy mã sản phẩm '{sku}' để xóa.")
                return False


def display_table(products: List[Tuple]):
    """In danh sách sản phẩm dạng bảng rõ ràng."""
    if not products:
        print("-> Không có dữ liệu để hiển thị.")
        return

    print("-" * 75)
    print(f"{'ID':<5} | {'Mã SKU':<12} | {'Tên sản phẩm':<25} | {'Số lượng':<10} | {'Đơn giá':<12}")
    print("-" * 75)
    for p in products:
        p_id, sku, name, qty, price = p
        print(f"{p_id:<5} | {sku:<12} | {name:<25} | {qty:<10} | {price:,.2f}")
    print("-" * 75)


def get_positive_int(prompt: str) -> int:
    while True:
        try:
            val = int(input(prompt))
            if val < 0:
                print("Giá trị phải lớn hơn hoặc bằng 0.")
                continue
            return val
        except ValueError:
            print("Vui lòng nhập một số nguyên hợp lệ.")


def get_positive_float(prompt: str) -> float:
    while True:
        try:
            val = float(input(prompt))
            if val < 0:
                print("Giá trị phải lớn hơn hoặc bằng 0.")
                continue
            return val
        except ValueError:
            print("Vui lòng nhập một số thực hợp lệ.")


def main():
    manager = InventoryManager()

    while True:
        print("\n=== HỆ THỐNG QUẢN LÝ KHO HÀNG ===")
        print("1. Xem danh sách hàng tồn kho")
        print("2. Thêm sản phẩm mới")
        print("3. Nhập kho (tăng số lượng)")
        print("4. Xuất kho (giảm số lượng)")
        print("5. Tìm kiếm sản phẩm")
        print("6. Xóa sản phẩm")
        print("0. Thoát")

        choice = input("Lựa chọn chức năng (0-6): ").strip()

        if choice == "1":
            print("\n--- DANH SÁCH TỒN KHO ---")
            display_table(manager.list_products())

        elif choice == "2":
            print("\n--- THÊM SẢN PHẨM MỚI ---")
            sku = input("Nhập mã SKU: ").strip()
            name = input("Nhập tên sản phẩm: ").strip()
            if not sku or not name:
                print("-> Mã SKU và tên không được để trống.")
                continue
            qty = get_positive_int("Nhập số lượng ban đầu: ")
            price = get_positive_float("Nhập đơn giá: ")
            manager.add_product(sku, name, qty, price)

        elif choice == "3":
            print("\n--- NHẬP HÀNG VÀO KHO ---")
            sku = input("Nhập mã SKU cần nhập thêm: ")
            amount = get_positive_int("Nhập số lượng nhập thêm: ")
            if amount > 0:
                manager.update_stock(sku, amount)

        elif choice == "4":
            print("\n--- XUẤT HÀNG KHỎI KHO ---")
            sku = input("Nhập mã SKU cần xuất: ")
            amount = get_positive_int("Nhập số lượng xuất: ")
            if amount > 0:
                manager.update_stock(sku, -amount)

        elif choice == "5":
            print("\n--- TÌM KIẾM SẢN PHẨM ---")
            kw = input("Nhập mã SKU hoặc tên sản phẩm cần tìm: ")
            results = manager.search_product(kw)
            display_table(results)

        elif choice == "6":
            print("\n--- XÓA SẢN PHẨM ---")
            sku = input("Nhập mã SKU muốn xóa: ")
            confirm = input(f"Bạn có chắc muốn xóa '{sku}'? (y/n): ").strip().lower()
            if confirm == "y":
                manager.delete_product(sku)

        elif choice == "0":
            print("Đã thoát chương trình.")
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng thử lại.")


if __name__ == "__main__":
    main()
