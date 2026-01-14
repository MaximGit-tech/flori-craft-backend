from collections import defaultdict
import re
import requests
from typing import Dict, List, Optional
from django.conf import settings
from .tokens import get_session


SIZE_PATTERN = re.compile(r"\s(S|M|L)$")
SIZE_ORDER = {"S": 0, "M": 1, "L": 2}

class PosifloraProductService:
    """Сервис для работы с товарами через Posiflora API (без пагинации)"""

    BASE_PATH = "/bouquets?page%5Bnumber%5D=1&page%5Bsize%5D=12&sort=-price&urlPath=floricraft"
    SHOP_API_BASE = "/shop/api/v1"

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

    def _build_shop_url(self, path: str) -> str:
        """Построить полный URL к Shop API"""
        base_url = getattr(settings, 'POSIFLORA_SHOP_URL', 'https://floricraft.posiflora.com')
        return f"{base_url}{self.SHOP_API_BASE}{path}"

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
        """Парсинг данных букета из формата JSON:API в удобный формат"""
        attributes = product_data.get("attributes", {})
        product_id = product_data.get("id")

        image_url = self._get_image_url_from_included(product_data, included)
        category_name = self._get_category_from_included(product_data, included)

        # SKU: берём docNo если есть, иначе сам id
        sku = attributes.get("docNo") or product_id

        # Цена из trueSaleAmount -> saleAmount -> amount (для букетов)
        price = attributes.get("trueSaleAmount") or attributes.get("saleAmount") or attributes.get("amount")

        # Доступность из поля public
        available = bool(attributes.get("public", False))

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
            "item_type": "bouquet",
            "price_min": price,
            "price_max": price,
            "amount": attributes.get("amount"),
            "sale_amount": attributes.get("saleAmount"),
            "true_sale_amount": attributes.get("trueSaleAmount"),
            "status": attributes.get("status"),
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


    def fetch_bouquets(self) -> List[Dict]:
        """
        Получить все букеты в простом формате для фронтенда

        Returns:
            Список букетов в формате:
            [
                {
                    "id": "uuid",
                    "title": "Букет с Амариллисами",
                    "description": "Описание букета",
                    "image_urls": ["url1", "url2", "url3"],
                    "price": 10200
                }
            ]
        """
        url = self._build_shop_url("/bouquets")
        params = {
            "page[number]": 1,
            "page[size]": 100,
            "sort": "-price",
            "urlPath": "floricraft"
        }

        response = requests.get(
            url,
            headers=self._get_headers(),
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

        bouquets_data = payload.get("data", [])
        result = []

        for bouquet in bouquets_data:
            bouquet_id = bouquet.get("id", "")
            attributes = bouquet.get("attributes", {})

            title = attributes.get("title", "")
            description = attributes.get("description", "")
            price = attributes.get("saleAmount", 0)

            # Собираем все доступные изображения
            image_urls = []
            if attributes.get("logo"):
                image_urls.append(attributes["logo"])
            if attributes.get("logoMedium"):
                image_urls.append(attributes["logoMedium"])
            if attributes.get("logoShop"):
                image_urls.append(attributes["logoShop"])

            result.append({
                "id": bouquet_id,
                "title": title,
                "description": description,
                "image_urls": image_urls,
                "price": price
            })

        return result

    def fetch_products_by_categories(self) -> Dict:
        """
        Получить все продукты, сгруппированные по категориям

        Returns:
            Словарь в формате:
            {
                "categories": [
                    {
                        "name": "Аксессуары для цветов",
                        "products": [
                            {
                                "title": "ваза керамика коричневая",
                                "description": "",
                                "image_urls": ["url1", "url2", "url3"],
                                "price": 4500
                            }
                        ]
                    }
                ]
            }
        """
        # Получаем все категории
        categories_url = self._build_shop_url("/categories")
        categories_params = {
            "urlPath": "floricraft"
        }

        categories_response = requests.get(
            categories_url,
            headers=self._get_headers(),
            params=categories_params,
        )
        categories_response.raise_for_status()
        categories_payload = categories_response.json()

        categories_data = categories_payload.get("data", [])
        result_categories = []

        # Для каждой категории получаем продукты
        for category in categories_data:
            category_id = category.get("id", "")
            category_attributes = category.get("attributes", {})
            category_name = category_attributes.get("title", "")

            # Пропускаем категории без продуктов
            if category_attributes.get("countProducts", 0) == 0:
                continue

            # Получаем продукты для этой категории
            products_url = self._build_shop_url("/products")
            products_params = {
                "page[number]": 1,
                "page[size]": 100,
                "filter[categories]": category_id,
                "sort": "-price",
                "urlPath": "floricraft"
            }

            products_response = requests.get(
                products_url,
                headers=self._get_headers(),
                params=products_params,
            )
            products_response.raise_for_status()
            products_payload = products_response.json()

            products_data = products_payload.get("data", [])

            # Группируем продукты по названию для поддержки вариантов размеров
            grouped_products = defaultdict(lambda: {
                "title": "",
                "description": "",
                "image_urls": set(),
                "variants": [],
                "price": None
            })

            for product in products_data:
                product_attributes = product.get("attributes", {})
                raw_title = product_attributes.get("title", "")
                description = product_attributes.get("description", "")
                price = product_attributes.get("price", 0)

                # Собираем изображения
                image_urls = []
                if product_attributes.get("logo"):
                    image_urls.append(product_attributes["logo"])
                if product_attributes.get("logoMedium"):
                    image_urls.append(product_attributes["logoMedium"])
                if product_attributes.get("logoShop"):
                    image_urls.append(product_attributes["logoShop"])

                # Проверяем, есть ли в названии размер (S, M, L)
                match = SIZE_PATTERN.search(raw_title)
                if match:
                    # Если есть размер - добавляем как вариант
                    size = match.group(1)
                    clean_title = SIZE_PATTERN.sub("", raw_title).strip()

                    product_group = grouped_products[clean_title]
                    product_group["title"] = clean_title
                    product_group["description"] = description
                    for img_url in image_urls:
                        product_group["image_urls"].add(img_url)
                    product_group["variants"].append({
                        "size": size,
                        "price": price
                    })
                else:
                    # Если размера нет - добавляем как обычный продукт
                    product_group = grouped_products[raw_title]
                    product_group["title"] = raw_title
                    product_group["description"] = description
                    for img_url in image_urls:
                        product_group["image_urls"].add(img_url)
                    product_group["price"] = price

            # Преобразуем сгруппированные продукты в финальный формат
            category_products = []
            for product_data in grouped_products.values():
                product_dict = {
                    "title": product_data["title"],
                    "description": product_data["description"],
                    "image_urls": list(product_data["image_urls"])
                }

                if product_data["variants"]:
                    # Сортируем варианты по размеру
                    sorted_variants = sorted(
                        product_data["variants"],
                        key=lambda v: SIZE_ORDER.get(v["size"], 999)
                    )
                    product_dict["variants"] = sorted_variants
                else:
                    product_dict["price"] = product_data["price"]

                category_products.append(product_dict)

            # Добавляем категорию только если в ней есть продукты
            if category_products:
                result_categories.append({
                    "name": category_name,
                    "products": category_products
                })

        return {"categories": result_categories}

    def fetch_products_from_posiflora(self):
        '''
        Получить букеты с группировкой по названию и размерам

        return:
        список словарей в формате:
        [
            {
                "title": "Букет роз",
                "description": "Красивый букет из роз",
                "image_urls": ["/images/rose_1.png", ...],
                "variants": [
                    {"size": "S", "price": 4500},
                    {"size": "M", "price": 5500},
                    {"size": "L", "price": 6500}
                ]
            }
        ]
        '''

        url = self._build_url(self.BASE_PATH)
        response = requests.get(
            url,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        payload = response.json()

        bouquets = payload.get("data", [])
        included = payload.get("included", [])

        grouped_products = defaultdict(lambda: {
            "title": "",
            "description": "",
            "image_urls": set(),
            "variants": []
        })

        for bouquet in bouquets:
            attrs = bouquet["attributes"]

            raw_title = attrs.get("title", "")
            description = attrs.get("description") or ""

            price = attrs.get("trueSaleAmount") or attrs.get("saleAmount") or attrs.get("amount", 0)
            price = float(price) if price else 0

            match = SIZE_PATTERN.search(raw_title)
            if not match:
                continue

            size = match.group(1)
            clean_title = SIZE_PATTERN.sub("", raw_title).strip()

            product = grouped_products[clean_title]
            product["title"] = clean_title
            product["description"] = description

            image_url = self._get_image_url_from_included(bouquet, included)
            if image_url:
                product["image_urls"].add(image_url)

            product["variants"].append({
                "size": size,
                "price": price,
            })

        result = []
        for product in grouped_products.values():
            # Сортируем варианты по размеру
            product["variants"] = sorted(
                product["variants"],
                key=lambda v: SIZE_ORDER.get(v["size"], 999)
            )

            if not product["variants"]:
                continue

            product["image_urls"] = list(product["image_urls"])

            result.append(product)

        return result



    def fetch_specifications(self) -> Dict:
        """
        Получить спецификации (букеты) с вариантами размеров из нового API

        Returns:
            Словарь в формате:
            {
                "categories": [
                    {
                        "name": "Авторские букеты",
                        "products": [
                            {
                                "title": "Букет Максим",
                                "description": "",
                                "image_urls": ["url1", "url2"],
                                "variants": [
                                    {"size": "S", "price": 4050},
                                    {"size": "M", "price": 3150}
                                ]
                            },
                            {
                                "title": "Ваза",
                                "description": "",
                                "image_urls": ["url1"],
                                "price": 4500
                            }
                        ]
                    }
                ]
            }
        """
        url = self._build_url("/specifications")
        params = {
            "include": "category,specVariants.variant,specVariants.variant.tags,specVariants.specVariantPrices,images",
            "filter[activeVariants]": "true",
            "filter[status]": "on"
        }

        response = requests.get(
            url,
            headers=self._get_headers(),
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

        specifications_data = payload.get("data", [])
        included = payload.get("included", [])

        # Создаем индекс included для быстрого поиска
        included_index = {}
        for item in included:
            key = (item.get("type"), item.get("id"))
            included_index[key] = item

        # Группируем продукты по категориям
        categories_dict = defaultdict(list)

        for spec in specifications_data:
            spec_id = spec.get("id")
            attributes = spec.get("attributes", {})
            relationships = spec.get("relationships", {})

            title = attributes.get("title", "")
            description = attributes.get("description", "")

            # Получаем категорию
            category_data = relationships.get("category", {}).get("data")
            if category_data:
                category_key = (category_data.get("type"), category_data.get("id"))
                category_obj = included_index.get(category_key)
                category_name = category_obj.get("attributes", {}).get("title", "") if category_obj else "Без категории"
            else:
                category_name = "Без категории"

            # Получаем изображения
            images_data = relationships.get("images", {}).get("data", [])
            image_urls = []
            for img_ref in images_data:
                img_key = (img_ref.get("type"), img_ref.get("id"))
                img_obj = included_index.get(img_key)
                if img_obj:
                    img_attrs = img_obj.get("attributes", {})
                    img_url = img_attrs.get("url") or img_attrs.get("original") or img_attrs.get("path")
                    if img_url:
                        image_urls.append(img_url)

            # Получаем варианты (specVariants)
            spec_variants_data = relationships.get("specVariants", {}).get("data", [])
            variants = []

            for spec_variant_ref in spec_variants_data:
                spec_variant_key = (spec_variant_ref.get("type"), spec_variant_ref.get("id"))
                spec_variant_obj = included_index.get(spec_variant_key)

                if not spec_variant_obj:
                    continue

                spec_variant_rels = spec_variant_obj.get("relationships", {})

                # Получаем название варианта (размер)
                variant_data = spec_variant_rels.get("variant", {}).get("data")
                if variant_data:
                    variant_key = (variant_data.get("type"), variant_data.get("id"))
                    variant_obj = included_index.get(variant_key)
                    if variant_obj:
                        size = variant_obj.get("attributes", {}).get("title", "")
                    else:
                        continue
                else:
                    continue

                # Получаем цену из specVariantPrices
                spec_variant_prices_data = spec_variant_rels.get("specVariantPrices", {}).get("data", [])
                price = None

                for price_ref in spec_variant_prices_data:
                    price_key = (price_ref.get("type"), price_ref.get("id"))
                    price_obj = included_index.get(price_key)
                    if price_obj:
                        price_attrs = price_obj.get("attributes", {})
                        # Берем первую доступную цену
                        if price_attrs.get("status") == "on":
                            price = price_attrs.get("priceValue") or price_attrs.get("compositionPrice")
                            break

                if price is not None and size:
                    variants.append({
                        "size": size,
                        "price": price
                    })

            # Формируем продукт
            product_dict = {
                "title": title,
                "description": description,
                "image_urls": image_urls
            }

            # Если есть варианты - добавляем их, иначе используем minPrice/maxPrice
            if variants:
                # Сортируем варианты по размеру
                sorted_variants = sorted(
                    variants,
                    key=lambda v: SIZE_ORDER.get(v["size"], 999)
                )
                product_dict["variants"] = sorted_variants
            else:
                # Если нет вариантов, используем minPrice или maxPrice
                min_price = attributes.get("minPrice")
                max_price = attributes.get("maxPrice")
                if min_price is not None or max_price is not None:
                    product_dict["price"] = min_price if min_price is not None else (max_price or 0)

            categories_dict[category_name].append(product_dict)

        # Преобразуем в итоговый формат
        result_categories = [
            {
                "name": category_name,
                "products": products
            }
            for category_name, products in categories_dict.items()
        ]

        return {"categories": result_categories}


def get_product_service() -> PosifloraProductService:
    """Получить экземпляр сервиса продуктов"""
    return PosifloraProductService()
