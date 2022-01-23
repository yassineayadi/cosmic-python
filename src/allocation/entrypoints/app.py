from datetime import datetime
from uuid import UUID

from flask import Blueprint, Flask, jsonify, redirect, request, url_for
from marshmallow import ValidationError

from allocation import messagebus, services, config

from allocation.core import commands, domain
from allocation.entrypoints import serializers

from allocation.entrypoints.serializers import DataLoader
from allocation.unit_of_work import UnitOfWork


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(config.get_config())
    app.register_blueprint(bp)
    return app


bp = Blueprint("api", __name__)


@bp.errorhandler(ValidationError)
def handle_validation_error(e: ValidationError):
    return jsonify(e.messages), 400


@bp.route("/", methods=["GET", "POST"])
def index():
    data = request.data

    return b"Index"


@bp.route("/allocate", methods=["POST"])
def allocate():
    data = request.json
    order_item_id = UUID(data["order_item_id"])
    sku_id = UUID(data["_sku_id"])
    cmd = commands.Allocate(sku_id, order_item_id)
    messagebus.handle([cmd], UnitOfWork())

    return redirect(url_for(".get_order_item", order_item_id=order_item_id))


@bp.route("/order_item/allocations/<uuid:order_item_id>", methods=["GET"])
def get_allocations():
    ...


@bp.route("/order_item/<uuid:order_item_id>", methods=["GET"])
def get_order_item(order_item_id):
    with UnitOfWork() as uow:
        order_items = uow.products.get_all_order_items()
        order_item = next(oi for oi in order_items if oi.uuid == order_item_id)
        return jsonify(serializers.OrderItem().dump(order_item))


@bp.route("/batch/<uuid:batch_id>", methods=["GET"])
def get_batch(batch_id):
    with UnitOfWork() as uow:
        batches = uow.products.get_all_batches()
        batch = next(b for b in batches if b.uuid == batch_id)
        return jsonify(serializers.Batch().dump(batch))


@bp.route("/batch/create", methods=["POST"])
def create_batch():
    data = request.json
    cmd = commands.CreateBatch(
        sku_id=data["sku_id"],
        quantity=data["quantity"],
        eta=datetime.fromtimestamp(data["eta"]),
    )
    batch_id = services.create_batch(cmd, UnitOfWork())
    response = redirect(url_for(".get_batch", batch_id=batch_id))
    return response


@bp.route("/product/create", methods=["POST"])
def create_product():
    with DataLoader(serializers.CreateSKU(), request) as data:
        sku = domain.create_sku(data["name"])
        cmd = commands.CreateProductCommand(sku)
        sku_id = services.create_product(cmd, UnitOfWork())
        return redirect(url_for(".get_product", sku_id=sku_id))


@bp.route("/product/<uuid:sku_id>", methods=["GET"])
def get_product(sku_id):
    with UnitOfWork() as uow:
        product = uow.products.get(sku_id)
        data = serializers.Product().dump(product)
        return jsonify(data)


@bp.route("/products", methods=["GET"])
def list_products():
    with UnitOfWork() as uow:
        products = uow.products.list()
        data = serializers.Product().dump(products, many=True)
        return jsonify(data)


@bp.route("/sku/create", methods=["POST"])
def create_sku():
    sku_name = serializers.CreateSKU().load(request.json)
    with UnitOfWork() as uow:
        sku = domain.create_sku(sku_name["name"])
        product = domain.create_product(sku)
        uow.products.add(product)
        return jsonify(serializers.SKU().dump(sku))


@bp.route("/skus", methods=["GET", "POST"])
def list_skus():
    with UnitOfWork() as uow:
        products = uow.products.list()
        skus = [product.sku for product in products]
        return jsonify(serializers.SKU(many=True).dump(skus))
