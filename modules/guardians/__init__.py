#modules/guardians/__init__.py

from flask import Blueprint

<<<<<<< HEAD
=======

>>>>>>> origin/guardians
guardians_bp = Blueprint(
    'guardians_bp', 
    __name__,
    template_folder='../templates', 
    static_folder='../static'       
)

admin_v2_bp = Blueprint(
    'admin_v2_bp', 
    __name__, 
    template_folder='../templates', 
    url_prefix='/admin-v2'
)


from . import routes
from . import admin_refactored_routes 
<<<<<<< HEAD
from . import admin_routes
from . import missions_logic
=======
from . import missions_logic
from . import my_profile
>>>>>>> origin/guardians
