# Título del proyecto

Modulo Webservices Odoo para comunicación con GETW1 CHILE

## Cómo empezar
Cargar Proyecto en el DIR: /usr/lib/python3.10/site-packages/odoo/addons_custom/bcn_getw1
En caso que no existe debe crear el dir con el comando: mkdir <nombre_dir>
Agregar Permisos del dir chmod 650

Agregar nombre del DIR en el archivo de configuración de Odoo: /etc/odoo/odoo.conf 
Concatenar el nuevo DIR en el campo addons_path: ejemplo:

addons_path = /usr/lib/python3.10/site-packages/odoo/addons,/usr/lib/python3.10/site-packages/odoo/addons_custom


## Comandos

Cargar Repositorio Proyecto:

git remote add origin http://gitbcn01.dtebcn.cl/dmunoz/odoo-getw1-chile.git

Reiniciar Modulo Odoo: /usr/bin/odoo -u <nombre_modulo> --stop-after-init;
ej: 
    /usr/bin/odoo -u bcn_getw1 --stop-after-init;

Reiniciar Odoo systemctl restart odoo.service



## Autores

Diego Muñoz J.
Jhonatan Rocha

## Licencia
OPL-1

