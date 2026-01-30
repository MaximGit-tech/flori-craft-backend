from collections import defaultdict
import re
from typing import Dict, List, Optional
from django.conf import settings
from .tokens import make_request_with_retry


SIZE_PATTERN = re.compile(r"\s(S|M|L)$")
SIZE_ORDER = {"S": 0, "M": 1, "L": 2}

class PosifloraProductService:
    """Сервис для работы с товарами через Posiflora API (без пагинации)"""

    BASE_PATH = "/bouquets?page%5Bnumber%5D=1&page%5Bsize%5D=12&sort=-price&urlPath=floricraft"
    SHOP_API_BASE = "/shop/api/v1"

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Получить базовые заголовки для запроса к API (без Authorization)"""
        return {
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
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

        sku = attributes.get("docNo") or product_id

        price = attributes.get("trueSaleAmount") or attributes.get("saleAmount") or attributes.get("amount")

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

        response = make_request_with_retry(
            'GET',
            url,
            headers=self._get_headers(),
            params=params,
            timeout=10
        )
        payload = response.json()

        bouquets_data = payload.get("data", [])
        result = []

        for bouquet in bouquets_data:
            bouquet_id = bouquet.get("id", "")
            attributes = bouquet.get("attributes", {})

            title = attributes.get("title", "")
            description = attributes.get("description", "")
            price = attributes.get("saleAmount", 0)

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

        response = make_request_with_retry(
            'GET',
            url,
            headers=self._get_headers(),
            params=params,
            timeout=10
        )
        payload = response.json()

        specifications_data = payload.get("data", [])
        included = payload.get("included", [])

        included_index = {}
        for item in included:
            key = (item.get("type"), item.get("id"))
            included_index[key] = item

        categories_dict = defaultdict(list)

        for spec in specifications_data:
            spec_id = spec.get("id")
            attributes = spec.get("attributes", {})
            relationships = spec.get("relationships", {})

            title = attributes.get("title", "")
            description = attributes.get("description", "")

            category_data = relationships.get("category", {}).get("data")
            if category_data:
                category_key = (category_data.get("type"), category_data.get("id"))
                category_obj = included_index.get(category_key)
                category_name = category_obj.get("attributes", {}).get("title", "") if category_obj else "Без категории"
            else:
                category_name = "Без категории"

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

            spec_variants_data = relationships.get("specVariants", {}).get("data", [])
            variants = []

            for spec_variant_ref in spec_variants_data:
                spec_variant_key = (spec_variant_ref.get("type"), spec_variant_ref.get("id"))
                spec_variant_obj = included_index.get(spec_variant_key)

                if not spec_variant_obj:
                    continue

                spec_variant_rels = spec_variant_obj.get("relationships", {})

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

                spec_variant_prices_data = spec_variant_rels.get("specVariantPrices", {}).get("data", [])
                price = None

                for price_ref in spec_variant_prices_data:
                    price_key = (price_ref.get("type"), price_ref.get("id"))
                    price_obj = included_index.get(price_key)
                    if price_obj:
                        price_attrs = price_obj.get("attributes", {})
                        if price_attrs.get("status") == "on":
                            price = price_attrs.get("priceValue") or price_attrs.get("compositionPrice")
                            break

                if price is not None and size:
                    variants.append({
                        "size": size,
                        "price": price
                    })

            product_dict = {
                "id": spec_id,
                "title": title,
                "description": description,
                "image_urls": image_urls
            }

            if variants:
                sorted_variants = sorted(
                    variants,
                    key=lambda v: SIZE_ORDER.get(v["size"], 999)
                )
                product_dict["variants"] = sorted_variants
            else:
                min_price = attributes.get("minPrice")
                max_price = attributes.get("maxPrice")
                if min_price is not None or max_price is not None:
                    product_dict["price"] = min_price if min_price is not None else (max_price or 0)

            categories_dict[category_name].append(product_dict)

        result_categories = [
            {
                "name": category_name,
                "products": products
            }
            for category_name, products in categories_dict.items()
        ]

        return {"categories": result_categories}

    def _parse_product_response(self, payload: Dict) -> Dict:
        """
        Парсинг ответа API в единый формат продукта

        Args:
            payload: JSON ответ от Posiflora API

        Returns:
            Словарь с данными продукта
        """
        spec = payload.get("data", {})
        included = payload.get("included", [])

        spec_id = spec.get("id")
        attributes = spec.get("attributes", {})
        relationships = spec.get("relationships", {})

        title = attributes.get("title", "")
        description = attributes.get("description", "")

        included_index = {}
        for item in included:
            key = (item.get("type"), item.get("id"))
            included_index[key] = item

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

        spec_variants_data = relationships.get("specVariants", {}).get("data", [])
        variants = []

        for spec_variant_ref in spec_variants_data:
            spec_variant_key = (spec_variant_ref.get("type"), spec_variant_ref.get("id"))
            spec_variant_obj = included_index.get(spec_variant_key)

            if not spec_variant_obj:
                continue

            spec_variant_rels = spec_variant_obj.get("relationships", {})

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

            spec_variant_prices_data = spec_variant_rels.get("specVariantPrices", {}).get("data", [])
            price = None

            for price_ref in spec_variant_prices_data:
                price_key = (price_ref.get("type"), price_ref.get("id"))
                price_obj = included_index.get(price_key)
                if price_obj:
                    price_attrs = price_obj.get("attributes", {})
                    if price_attrs.get("status") == "on":
                        price = price_attrs.get("priceValue") or price_attrs.get("compositionPrice")
                        break

            if price is not None and size:
                variants.append({
                    "size": size,
                    "price": price
                })

        product_dict = {
            "id": spec_id,
            "title": title,
            "description": description,
            "image_urls": image_urls
        }

        if variants:
            sorted_variants = sorted(
                variants,
                key=lambda v: SIZE_ORDER.get(v["size"], 999)
            )
            product_dict["variants"] = sorted_variants
        else:
            min_price = attributes.get("minPrice")
            max_price = attributes.get("maxPrice")
            if min_price is not None or max_price is not None:
                product_dict["price"] = min_price if min_price is not None else (max_price or 0)

        return product_dict

    def get_specification_by_id(self, product_id: str) -> Dict:
        """
        Получить конкретную спецификацию (букет) по ID в формате CategoryProductSerializer

        Сначала ищет в /specifications, если не найдено - ищет в /bouquets

        Args:
            product_id: ID спецификации или букета

        Returns:
            Данные продукта в формате:
            {
                "id": "uuid",
                "title": "Букет Максим",
                "description": "",
                "image_urls": ["url1", "url2"],
                "variants": [
                    {"size": "S", "price": 4050},
                    {"size": "M", "price": 3150}
                ]
            }
            или
            {
                "id": "uuid",
                "title": "Ваза",
                "description": "",
                "image_urls": ["url1"],
                "price": 4500
            }
        """
        import requests

        try:
            url = self._build_url(f"/specifications/{product_id}")
            params = {
                "include": "category,specVariants.variant,specVariants.variant.tags,specVariants.specVariantPrices,images",
            }

            response = make_request_with_retry(
                'GET',
                url,
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            payload = response.json()
            return self._parse_product_response(payload)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                try:
                    url = self._build_shop_url(f"/bouquets/{product_id}")
                    params = {
                        "include": "category,specVariants.variant,specVariants.variant.tags,specVariants.specVariantPrices,images",
                    }

                    response = make_request_with_retry(
                        'GET',
                        url,
                        headers=self._get_headers(),
                        params=params,
                        timeout=10
                    )
                    payload = response.json()
                    return self._parse_product_response(payload)

                except requests.exceptions.HTTPError as bouquet_error:
                    raise RuntimeError(f"Product with id {product_id} not found in specifications or bouquets")

            raise 



def get_product_service() -> PosifloraProductService:
    """Получить экземпляр сервиса продуктов"""
    return PosifloraProductService()
