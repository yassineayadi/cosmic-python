from datetime import datetime
from uuid import UUID

from flask import Blueprint, Flask, Response, redirect, request, url_for

from allocation import messagebus, services
from allocation.core import commands, domain
from allocation.interfaces.database.db import session_factory
from allocation.interfaces.serializers import (
    BatchSchema,
    CreateSKUSchema,
    OrderItemSchema,
    SKUSchema,
)
from allocation.unit_of_work import UnitOfWork


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
    order_item_id = UUID(order_data["order_item_id"])
    sku_id = UUID(order_data["_sku_id"])
    cmd = commands.Allocate(sku_id, order_item_id)
    messagebus.handle([cmd], UnitOfWork())

    return redirect(url_for(".get_order_item", order_item_id=order_item_id))


@bp.route("/order_item/allocations/<uuid:order_ite_id>", methods=["GET"])
def get_allocations():
    ...


@bp.route("/order_item/<uuid:order_item_id>", methods=["GET"])
def get_order_item(order_item_id):

    with UnitOfWork() as uow:
        order_items = uow.products.get_all_order_items()
        order_item = next(oi for oi in order_items if oi.uuid == order_item_id)
        return Response(
            response=OrderItemSchema().dumps(order_item), mimetype="application/json"
        )


@bp.route("/batch/<uuid:batch_id>", methods=["GET"])
def get_batch(batch_id):
    with UnitOfWork(session_factory) as uow:
        batches = uow.products.get_all_batches()
        batch = next(b for b in batches if b.uuid == batch_id)
        return Response(
            response=BatchSchema().dumps(batch),
            mimetype="application/json",
        )


@bp.route("/batch/create", methods=["POST"])
def create_batch():
    data = request.json
    cmd = commands.CreateBatch(
        sku_id=data["sku_id"],
        quantity=data["quantity"],
        eta=datetime.fromtimestamp(data["eta"]),
    )
    batch_id = services.create_batch(cmd, UnitOfWork(session_factory))
    response = redirect(url_for(".get_batch", batch_id=batch_id))
    return response


@bp.route("/order/create", methods=["POST"])
def create_order():
    ...


@bp.route("/sku/create", methods=["POST"])
def create_sku():
    create_sku_request = CreateSKUSchema().load(request.json)
    sku_list = create_sku_request["sku_names"]
    skus = [domain.create_sku(sku_name) for sku_name in sku_list]
    with UnitOfWork() as uow:
        uow.products.add_all(skus)

    return Response(
        response=SKUSchema(many=True).dumps(skus), mimetype="application/json"
    )


@bp.route("/skus", methods=["GET"])
def list_skus():

    with UnitOfWork() as uow:
        products = uow.products.list()
        skus = [product.sku for product in products]

        return Response(
            response=SKUSchema(many=True).dumps(skus), mimetype="application/json"
        )
