import serial
import asyncio
import websockets
import json


SERIAL_PORT = 'COM3'  
BAUD_RATE = 9600


WS_HOST = 'localhost'
WS_PORT = 5001  # changed to 5001 to avoid conflict with flask


connected_clients = set()

async def handle_websocket(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def read_serial():
    try:
   
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to Arduino on {SERIAL_PORT}")
        
        last_activity_time = asyncio.get_event_loop().time()
        INACTIVITY_THRESHOLD = 2.0  
        
        while True:
            if ser.in_waiting:
                
                line = ser.readline().decode('utf-8').strip()
                print(f"Received from Arduino: {line}")
                
          
                last_activity_time = asyncio.get_event_loop().time()
           
                if connected_clients:
                    for client in connected_clients:
                        try:
                            await client.send(line)
                        except websockets.exceptions.ConnectionClosed:
                            connected_clients.remove(client)
            else:
              
                current_time = asyncio.get_event_loop().time()
                if current_time - last_activity_time > INACTIVITY_THRESHOLD:
              
                    no_movement_msg = "0,0,0.000000 - no significant movement"
                    if connected_clients:
                        for client in connected_clients:
                            try:
                                await client.send(no_movement_msg)
                            except websockets.exceptions.ConnectionClosed:
                                connected_clients.remove(client)
            
            await asyncio.sleep(0.1) 
            
    except serial.SerialException as e:
        print(f"Error connecting to Arduino: {e}")
    except Exception as e:
        print(f"Error in serial reading: {e}")

async def main():
    
    server = await websockets.serve(handle_websocket, WS_HOST, WS_PORT)
    print(f"WebSocket server started on ws://{WS_HOST}:{WS_PORT}")
    
    serial_task = asyncio.create_task(read_serial())
    
    try:
        await asyncio.gather(server.wait_closed(), serial_task)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main()) 