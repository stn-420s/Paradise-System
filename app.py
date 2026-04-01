from flask import Flask, render_template, request, redirect, url_for
import pyodbc
import json

app = Flask(__name__)

def obtener_conexion():
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=192.168.78.100;DATABASE=Paradise_DB;UID=Paradise_User;PWD=VasoConLeche123;TrustServerCertificate=yes;'
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def inicio():
    conexion = obtener_conexion()
    estado_db = "🟢 Conectado" if conexion else "🔴 Error de conexión"
    if conexion: conexion.close()
    
    # Recibimos mensajes de éxito de Ventas o de Movimientos
    id_exito = request.args.get('exito')
    msg_mov = request.args.get('msg_mov')
    
    mensaje = None
    if id_exito:
        mensaje = f"✅ ¡Factura #{id_exito} registrada con éxito!"
    elif msg_mov:
        mensaje = f"✅ ¡{msg_mov}!"
    
    return render_template('index.html', estado=estado_db, mensaje=mensaje)

@app.route('/ventas', methods=['GET', 'POST'])
def ventas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    mensaje = None

    if request.method == 'POST':
        carrito_json = request.form['carrito_datos']
        metodo_pago = request.form['metodo_pago']
        
        if carrito_json:
            carrito = json.loads(carrito_json)
            total_venta = sum(float(item['precio']) * int(item['unidades']) for item in carrito)

            try:
                cursor.execute("""
                    INSERT INTO Facturas (Metodo_Pago, Total_Factura) 
                    OUTPUT INSERTED.ID_Factura 
                    VALUES (?, ?)
                """, (metodo_pago, total_venta))
                id_nueva_factura = cursor.fetchone()[0]

                for item in carrito:
                    cursor.execute("""
                        INSERT INTO Ventas (ID_Factura, ID_Producto, Unidades, Precio_Vendido, Metodo_Pago)
                        VALUES (?, ?, ?, ?, ?)
                    """, (id_nueva_factura, item['id_producto'], item['unidades'], item['precio'], metodo_pago))
                
                conexion.commit()
                conexion.close()
                return redirect(url_for('inicio', exito=id_nueva_factura))
                
            except Exception as e:
                mensaje = f"❌ Error: {e}"

    cursor.execute("SELECT ID_Producto, Nombre FROM Productos ORDER BY Nombre")
    lista_productos = cursor.fetchall()
    conexion.close()

    return render_template('ventas.html', productos=lista_productos, mensaje=mensaje)

@app.route('/inventario')
def inventario():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Quitamos el Costo_Base y ordenamos por ID_Producto de forma ascendente (ASC)
    cursor.execute("SELECT ID_Producto, Nombre, Stock_Actual FROM Productos ORDER BY ID_Producto ASC")
    lista_inventario = cursor.fetchall()
    conexion.close()
    
    return render_template('inventario.html', inventario=lista_inventario)

@app.route('/movimientos', methods=['GET', 'POST'])
def movimientos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    mensaje = None

    if request.method == 'POST':
        # Recibimos la lista de movimientos desde el HTML
        movimientos_json = request.form.get('movimientos_datos')
        
        if movimientos_json:
            lista_movimientos = json.loads(movimientos_json)
            try:
                for item in lista_movimientos:
                    tipo = item['tipo']
                    id_prod = item['id_producto']
                    cantidad = int(item['cantidad'])
                    comentario = item['comentario']

                    # 1. Guardar en el historial
                    cursor.execute("""
                        INSERT INTO Movimientos_Inventario (Tipo_Movimiento, ID_Producto, Cantidad, Comentario)
                        VALUES (?, ?, ?, ?)
                    """, (tipo, id_prod, cantidad, comentario))
                    
                    # 2. Actualizar el Stock
                    if tipo == 'Ingreso':
                        cursor.execute("UPDATE Productos SET Stock_Actual = Stock_Actual + ? WHERE ID_Producto = ?", (cantidad, id_prod))
                    elif tipo == 'Egreso':
                        cursor.execute("UPDATE Productos SET Stock_Actual = Stock_Actual - ? WHERE ID_Producto = ?", (cantidad, id_prod))
                
                conexion.commit()
                conexion.close()
                # Lo mandamos al inicio con un mensaje de éxito
                return redirect(url_for('inicio', msg_mov="Movimientos de inventario registrados correctamente"))
            except Exception as e:
                mensaje = f"❌ Error: {e}"

    # Solo traemos los productos para la lista desplegable (ya no traemos el historial)
    cursor.execute("SELECT ID_Producto, Nombre FROM Productos ORDER BY Nombre")
    lista_productos = cursor.fetchall()
    conexion.close()
    
    return render_template('movimientos.html', productos=lista_productos, mensaje=mensaje)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)