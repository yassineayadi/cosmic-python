import flasgger
import marshmallow as ma
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from cachy import serializers
from flask import Blueprint, Flask, jsonify, redirect, request, url_for

import allocation.repositories
from allocation import config, messagebus, services
from allocation.core import commands, domain
from allocation.entrypoints import serializers
from allocation.unit_of_work import UnitOfWork


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(config.get_config())
    app.register_blueprint(bp)

    template = spec.to_flasgger(app, definitions=serializers.definitions)
    flasgger.Swagger(app, template=template)
    return app


spec = flasgger.APISpec(
    title="Allocation Service",
    version="1.0",
    openapi_version="2.0",
    plugins=(FlaskPlugin(), MarshmallowPlugin()),
)


bp = Blueprint("api", __name__)


@bp.errorhandler(ma.ValidationError)
def handle_validation_error(e: ma.ValidationError):
    """Handles marshmallow ValidationError.

    Returns 400 HTTP Response and field level error details."""
    return jsonify(e.messages), 400


@bp.errorhandler(allocation.repositories.InvalidSKU)
def handle_validator_error(e: allocation.repositories.InvalidSKU):
    """Handles InvalidSKUError.

    Returns 404 HTTP Response, if action is performed on SKUs not tracked in the repository."""
    return jsonify(e.args), 404


@bp.route("/", methods=["GET", "POST"])
def index():
    return redirect("/apidocs/")


@bp.route("/allocate", methods=["POST"])
def allocate():
    """Allocates an order item to an available batch.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/Allocate'
    responses:
      302:
        schema:
          $ref: '#/definitions/OrderItem'
    tags:
      - order items
    """
    with serializers.Validate(serializers.Allocate(), request) as data:
        cmd = commands.Allocate(**data)
        messagebus.handle([cmd], UnitOfWork())
        return redirect(url_for(".get_order_item", order_item_id=data["order_item_id"]))


@bp.route("/order_item/allocations/<uuid:order_item_id>", methods=["GET"])
def get_allocations():
    ...


@bp.route("/order_item/<uuid:order_item_id>", methods=["GET"])
def get_order_item(order_item_id):
    """Gets an order item.
    ---
    parameters:
      - in: path
        name: order_item_id
        required: true
        schema:
          type: string
    responses:
      200:
        schema:
          $ref: '#/definitions/OrderItem'
    tags:
      - order items
    """
    with UnitOfWork() as uow:
        order_items = uow.products.get_all_order_items()
        order_item = next(oi for oi in order_items if oi.uuid == order_item_id)
        return jsonify(serializers.OrderItem().dump(order_item))


@bp.route("/order_item", methods=["DELETE"])
def delete_order_item():
    """Deletes an order item.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/DiscardOrderItem'
    responses:
      200:
        description: OK
    tags:
     - order items
    """
    with serializers.Validate(serializers.DiscardOrderItem(), request) as data:
        cmd = commands.DiscardOrderItem(**data)
        services.discard_order_item(cmd, UnitOfWork())
        return "OK", 200


@bp.route("/batch/<uuid:batch_id>", methods=["GET"])
def get_batch(batch_id):
    """Gets a batch.
    ---
    parameters:
      - in: path
        name: batch_id
        required: true
        schema:
          type: string
    responses:
      200:
        description: a batch to be returned
        schema:
          $ref: '#/definitions/Batch'
    tags:
      - batches
    """
    with UnitOfWork() as uow:
        batches = uow.products.get_all_batches()
        batch = next(b for b in batches if b.uuid == batch_id)
        return jsonify(serializers.Batch().dump(batch))


@bp.route("/batch", methods=["POST"])
def create_batch():
    """Creates a new batch.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/CreateBatch'
    responses:
      302:
        schema:
          $ref: '#/definitions/Batch'
    tags:
      - batches
    """
    with serializers.Validate(serializers.CreateBatch(), request) as data:
        cmd = commands.CreateBatch(**data)
        batch_id = services.create_batch(cmd, UnitOfWork())
        response = redirect(url_for(".get_batch", batch_id=batch_id))
        return response


@bp.route("/product", methods=["POST"])
def create_product():
    """Creates a new product.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/CreateSKU'
    responses:
      302:
        schema:
          $ref: '#/definitions/Product'
    tags:
      - products
    """
    with serializers.Validate(serializers.CreateSKU(), request) as data:
        sku = domain.create_sku(**data)
        cmd = commands.CreateProductCommand(sku)
        sku_id = services.create_product(cmd, UnitOfWork())
        return redirect(url_for(".get_product", sku_id=sku_id))


@bp.route("/product/<uuid:sku_id>", methods=["GET"])
def get_product(sku_id):
    """Gets a product by SKU ID.
    ---
    parameters:
      - in: path
        name: sku_id
        required: true
        schema:
          type: string
    responses:
      200:
        schema:
          $ref: '#/definitions/Product'
    tags:
      - products
    """
    with UnitOfWork() as uow:
        product = uow.products.get(sku_id)
        data = serializers.Product().dump(product)
        return jsonify(data)


@bp.route("/products", methods=["GET"])
def list_products():
    """Lists all products.
    ---
    responses:
      200:
        schema:
          type: 'array'
          items:
            $ref: '#/definitions/Product'
    tags:
      - products
    """
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
