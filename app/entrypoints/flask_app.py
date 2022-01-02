from flask import Blueprint, Flask, Response, request
from test_repo import get_current_repo

from app.core import domain
from app.core.domain import SKU, Batch
from app.repositories import UnitofWork
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
    order_item = OrderItemSchema().load(order_data)
    repo = get_current_repo()
    with UnitofWork(repo) as uow:
        order_item = uow.repo.merge(order_item)
        batches = uow.repo.list(Batch)
        for batch in batches:
            batch.allocate_available_quantity(order_item)

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
    repo = get_current_repo()
    with UnitofWork(repo) as uow:
        uow.repo.add_all(skus)

    return Response(
        response=SKUSchema(many=True).dumps(skus), mimetype="application/json"
    )


@bp.route("/skus", methods=["GET"])
def list_skus():
    repo = get_current_repo()
    with UnitofWork(repo) as uow:
        skus = uow.repo.list(SKU)

    return Response(
        response=SKUSchema(many=True).dumps(skus), mimetype="application/json"
    )
