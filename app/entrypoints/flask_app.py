import json

from flask import Blueprint, Flask, Response, request

from app.core import domain
from app.core.domain import SKU, Batch, create_order_item
from app.interfaces import session_factory
from app.repositories import UnitOfWork
from app.serializers.domain import CreateSKUSchema, OrderItemSchema, SKUSchema


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


bp = Blueprint("api", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():

    data = request.data

    return b"Index"


@bp.route("/allocate", methods=["POST"])
def allocate():

    order_data = request.json
    # repo = get_current_repo()
    with UnitOfWork(session_factory) as uow:
        product = uow.products.get(order_data["_sku_id"])
        order_item = create_order_item(product.sku,order_data["quantity"])
        # order_item = OrderItemSchema().load(order_data)
        # order_item = uow.products.session.merge(order_item)
        product.allocate(order_item)

        return Response(
            response=OrderItemSchema().dumps(order_item),
            mimetype="application/json",
        )


@bp.route("/order/create", methods=["POST"])
def create_order():
    ...


@bp.route("/sku/create", methods=["POST"])
def create_sku():
    create_sku_request = CreateSKUSchema().load(request.json)
    sku_list = create_sku_request["sku_names"]
    skus = [domain.create_sku(sku_name) for sku_name in sku_list]
    with UnitOfWork(session_factory) as uow:
        uow.products.add_all(skus)

    return Response(
        response=SKUSchema(many=True).dumps(skus), mimetype="application/json"
    )


@bp.route("/skus", methods=["GET"])
def list_skus():

    with UnitOfWork(session_factory) as uow:
        products = uow.products.list()
        skus = [product.sku for product in products]

        return Response(
            response=SKUSchema(many=True).dumps(skus), mimetype="application/json"
        )
