"""WebSocket endpoints for real-time updates"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.redis import get_redis

router = APIRouter()


@router.websocket("/scan/{scan_id}")
async def websocket_scan_updates(websocket: WebSocket, scan_id: str):
    """
    WebSocket endpoint for real-time scan updates
    
    Streams events from Redis Stream to connected clients
    """
    await websocket.accept()
    
    redis = await get_redis()
    stream_key = f"scan:{scan_id}:events"
    last_id = '0'  # Start from beginning
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "scan_id": scan_id,
            "message": "WebSocket connection established"
        })
        
        while True:
            # Read new events from Redis Stream
            try:
                # XREAD with BLOCK to wait for new messages
                events = await redis.xread(
                    {stream_key: last_id},
                    count=10,
                    block=1000  # Block for 1 second
                )
                
                if events:
                    for stream, messages in events:
                        for message_id, message_data in messages:
                            last_id = message_id
                            
                            # Parse and send event
                            event_json = message_data.get('data', '{}')
                            event = json.loads(event_json)
                            
                            await websocket.send_json(event)
                
                # Check if client is still connected
                try:
                    await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    pass  # No message from client, continue
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error in WebSocket stream: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                break
    
    except WebSocketDisconnect:
        print(f"Client disconnected from scan {scan_id}")
    finally:
        try:
            await websocket.close()
        except:
            pass
