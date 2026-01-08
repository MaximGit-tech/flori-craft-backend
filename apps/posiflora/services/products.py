import requests
from typing import Dict, List, Optional
from django.conf import settings
from .tokens import get_session


class PosifloraProductService:
    """Сервис для работы с товарами через Posiflora API (без пагинации)"""

    BASE_PATH = "/inventory-items"

    def __init__(self):
        self.session = get_session()

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для запроса к API"""
        return {
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
            "Authorization": f"Bearer {self.session.access_token}",
        }

    def _build_url(self, path: str) -> str:
        """Построить полный URL к API"""
        base_url = getattr(settings, 'POSIFLORA_URL', 'https://floricraft.posiflora.com/api/v1')
        return f"{base_url}{path}"

    def _get_image_url_from_included(
        self, product_data: Dict, included: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """Извлечь URL изображения из relationships -> logo -> included"""
        if not included:
            return None

        relationships = product_data.get("relationships", {})
        logo_rel = relationships.get("logo", {}).get("data")
        if not logo_rel:
            return None

        logo_id = logo_rel.get("id")
        logo_type = logo_rel.get("type")

        for inc in included:
            if inc.get("type") == logo_type and inc.get("id") == logo_id:
                attrs = inc.get("attributes", {})
                return (
                    attrs.get("url")
                    or attrs.get("original")
                    or attrs.get("path")
                )

        return None

    def _get_category_from_included(
        self, product_data: Dict, included: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """Извлечь название категории из relationships -> category -> included"""
        if not included:
            return None

        relationships = product_data.get("relationships", {})
        category_rel = relationships.get("category", {}).get("data")
        if not category_rel:
            return None

        cat_id = category_rel.get("id")
        cat_type = category_rel.get("type")

        for inc in included:
            if inc.get("type") == cat_type and inc.get("id") == cat_id:
                return inc.get("attributes", {}).get("title")

        return None

    def _parse_product(self, product_data: Dict, included: Optional[List[Dict]] = None) -> Dict:
        """Парсинг данных товара из формата JSON:API в удобный формат"""
        attributes = product_data.get("attributes", {})
        product_id = product_data.get("id")

        image_url = self._get_image_url_from_included(product_data, included)
        category_name = self._get_category_from_included(product_data, included)

        # SKU: берём globalId если есть, иначе сам id
        sku = attributes.get("globalId") or product_id

        # Цена из priceMin/priceMax
        price = attributes.get("priceMin") or attributes.get("priceMax")

        # Доступность из поля public
        available = bool(attributes.get("public", True))

        return {
            "id": product_id,
            "name": attributes.get("title", "") or "",
            "description": attributes.get("description") or "",
            "sku": sku,
            "price": price,
            "currency": "RUB",
            "available": available,
            "image_url": image_url,
            "category": category_name or "",
            "item_type": attributes.get("itemType"),
            "price_min": attributes.get("priceMin"),
            "price_max": attributes.get("priceMax"),
        }

    def get_all_products(
        self,
        public_only: bool = True,
        on_window: Optional[bool] = None,
    ) -> List[Dict]:
        """
        Получить ВСЕ товары из API (проходит по всем страницам)

        Args:
            public_only: Только публичные товары
            on_window: Фильтр по витрине (True/False/None)

        Returns:
            Список всех товаров
        """
        all_items: List[Dict] = []
        page_number = 1
        page_size = 100

        while True:
            url = self._build_url(self.BASE_PATH)
            params = {
                "page[number]": page_number,
                "page[size]": page_size,
            }

            if public_only:
                params["public"] = "true"
            if on_window is not None:
                params["filter[onWindow]"] = "true" if on_window else "false"

            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

            data = payload.get("data", [])
            if not data:
                break

            included = payload.get("included", [])

            # Парсим каждый товар
            for item in data:
                parsed = self._parse_product(item, included)
                all_items.append(parsed)

            # Проверяем, есть ли следующая страница
            meta_page = payload.get("meta", {}).get("page", {})
            current = meta_page.get("number") or page_number
            size = meta_page.get("size") or page_size
            total = meta_page.get("total")

            if total is not None and current * size >= total:
                break

            page_number += 1

        return all_items

    def get_product_by_id(self, product_id: str) -> Dict:
        """
        Получить конкретный товар по ID

        Args:
            product_id: ID товара в Posiflora

        Returns:
            Данные товара
        """
        url = self._build_url(f"{self.BASE_PATH}/{product_id}")

        response = requests.get(
            url,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        payload = response.json()

        product_data = payload.get("data", {})
        included = payload.get("included", [])

        return self._parse_product(product_data, included)


def get_product_service() -> PosifloraProductService:
    """Получить экземпляр сервиса продуктов"""
    return PosifloraProductService()
