-- 1. Creamos la base de datos
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'Paradise_DB')
BEGIN
    CREATE DATABASE Paradise_DB;
END
GO

USE Paradise_DB;
GO

-- 2. Tabla de Catálogo (La base de todo)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Productos]') AND type in (N'U'))
BEGIN
    CREATE TABLE Productos (
        ID_Producto INT PRIMARY KEY IDENTITY(1,1),
        Nombre NVARCHAR(100) UNIQUE NOT NULL,
        Costo_Base DECIMAL(18,2), 
        Stock_Actual INT DEFAULT 0
    );
END

-- 3. Tabla de Facturas (Cabecera de recibos)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Facturas]') AND type in (N'U'))
BEGIN
    CREATE TABLE Facturas (
        ID_Factura INT IDENTITY(1,1) PRIMARY KEY,
        Fecha DATETIME DEFAULT GETDATE(),
        Metodo_Pago VARCHAR(50),
        Total_Factura DECIMAL(10,2)
    );
END

-- 4. Tabla de Ventas (Detalle de cada venta)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Ventas]') AND type in (N'U'))
BEGIN
    CREATE TABLE Ventas (
        ID_Venta INT PRIMARY KEY IDENTITY(1,1),
        Fecha DATETIME DEFAULT GETDATE(),
        ID_Producto INT FOREIGN KEY REFERENCES Productos(ID_Producto),
        ID_Factura INT FOREIGN KEY REFERENCES Facturas(ID_Factura), -- Amarrada a Facturas
        Unidades INT NOT NULL,
        Precio_Vendido DECIMAL(18,2) NOT NULL, 
        Metodo_Pago NVARCHAR(50) 
    );
END

-- 5. Tabla de Movimientos e Ingresos
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Movimientos_Inventario]') AND type in (N'U'))
BEGIN
    CREATE TABLE Movimientos_Inventario (
        ID_Movimiento INT IDENTITY(1,1) PRIMARY KEY,
        Fecha DATETIME DEFAULT GETDATE(),
        Tipo_Movimiento VARCHAR(20), -- 'Ingreso' o 'Egreso'
        ID_Producto INT FOREIGN KEY REFERENCES Productos(ID_Producto),
        Cantidad INT,
        Comentario VARCHAR(255)
    );
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Ingresos]') AND type in (N'U'))
BEGIN
    CREATE TABLE Ingresos (
        ID_Ingreso INT PRIMARY KEY IDENTITY(1,1),
        Fecha DATETIME DEFAULT GETDATE(),
        ID_Producto INT FOREIGN KEY REFERENCES Productos(ID_Producto),
        Unidades INT NOT NULL,
        Tipo_Cuadre NVARCHAR(50) 
    );
END
GO

-- 6. AUTOMATIZACIÓN: Triggers para el Stock
GO
CREATE OR ALTER TRIGGER TR_RestarStock ON Ventas AFTER INSERT AS
BEGIN
    UPDATE Productos 
    SET Stock_Actual = Stock_Actual - i.Unidades
    FROM Productos p 
    INNER JOIN inserted i ON p.ID_Producto = i.ID_Producto;
END;
GO

CREATE OR ALTER TRIGGER TR_SumarStock ON Ingresos AFTER INSERT AS
BEGIN
    UPDATE Productos 
    SET Stock_Actual = Stock_Actual + i.Unidades
    FROM Productos p 
    INNER JOIN inserted i ON p.ID_Producto = i.ID_Producto;
END;
GO