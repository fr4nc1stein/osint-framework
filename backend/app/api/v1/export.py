"""Export API - Export scan results in various formats"""
import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.scan import Scan
from app.services.graph_service import GraphService

router = APIRouter()


@router.get("/{scan_id}/json")
async def export_json(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Export scan results as JSON"""
    
    # Verify scan exists
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    # Get graph data
    graph_service = GraphService(db)
    graph_data = await graph_service.get_scan_graph(scan_id)
    
    # Build export data
    export_data = {
        "scan": {
            "id": str(scan.id),
            "seed_value": scan.seed_value,
            "seed_kind": scan.seed_kind,
            "status": scan.status,
            "modules": scan.modules,
            "created_at": scan.created_at.isoformat(),
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "finished_at": scan.finished_at.isoformat() if scan.finished_at else None,
        },
        "graph": graph_data,
        "stats": {
            "total_nodes": len(graph_data["nodes"]),
            "total_edges": len(graph_data["edges"]),
            "progress": f"{scan.progress}/{scan.total_modules}"
        }
    }
    
    # Return as JSON download
    json_str = json.dumps(export_data, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_str.encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=scan_{scan_id}.json"
        }
    )


@router.get("/{scan_id}/csv")
async def export_csv(
    scan_id: uuid.UUID,
    export_type: str = "edges",  # "edges" or "nodes"
    db: AsyncSession = Depends(get_db)
):
    """Export scan results as CSV (edges or nodes)"""
    
    # Verify scan exists
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    # Get graph data
    graph_service = GraphService(db)
    graph_data = await graph_service.get_scan_graph(scan_id)
    
    # Create CSV
    output = io.StringIO()
    
    if export_type == "edges":
        writer = csv.DictWriter(output, fieldnames=[
            "id", "source", "target", "relationship", "confidence", "source_module"
        ])
        writer.writeheader()
        
        for edge in graph_data["edges"]:
            writer.writerow({
                "id": edge["id"],
                "source": edge["source"],
                "target": edge["target"],
                "relationship": edge["relationship"],
                "confidence": edge["confidence"],
                "source_module": edge["source_module"]
            })
    
    else:  # nodes
        writer = csv.DictWriter(output, fieldnames=[
            "id", "kind", "value", "label", "confidence"
        ])
        writer.writeheader()
        
        for node in graph_data["nodes"]:
            writer.writerow({
                "id": node["id"],
                "kind": node["kind"],
                "value": node["value"],
                "label": node["label"],
                "confidence": node.get("confidence", "")
            })
    
    # Return as CSV download
    csv_content = output.getvalue()
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=scan_{scan_id}_{export_type}.csv"
        }
    )


@router.get("/{scan_id}/graphml")
async def export_graphml(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Export scan results as GraphML (for graph visualization tools)"""
    
    # Verify scan exists
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    # Get graph data
    graph_service = GraphService(db)
    graph_data = await graph_service.get_scan_graph(scan_id)
    
    # Build GraphML
    graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
    graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
    graphml.append('  <key id="kind" for="node" attr.name="kind" attr.type="string"/>')
    graphml.append('  <key id="value" for="node" attr.name="value" attr.type="string"/>')
    graphml.append('  <key id="relationship" for="edge" attr.name="relationship" attr.type="string"/>')
    graphml.append('  <key id="confidence" for="edge" attr.name="confidence" attr.type="double"/>')
    graphml.append('  <graph id="G" edgedefault="directed">')
    
    # Add nodes
    for node in graph_data["nodes"]:
        graphml.append(f'    <node id="{node["id"]}">')
        graphml.append(f'      <data key="kind">{node["kind"]}</data>')
        graphml.append(f'      <data key="value">{node["value"]}</data>')
        graphml.append('    </node>')
    
    # Add edges
    for edge in graph_data["edges"]:
        graphml.append(f'    <edge source="{edge["source"]}" target="{edge["target"]}">')
        graphml.append(f'      <data key="relationship">{edge["relationship"]}</data>')
        graphml.append(f'      <data key="confidence">{edge["confidence"]}</data>')
        graphml.append('    </edge>')
    
    graphml.append('  </graph>')
    graphml.append('</graphml>')
    
    graphml_content = '\n'.join(graphml)
    
    return StreamingResponse(
        io.BytesIO(graphml_content.encode()),
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename=scan_{scan_id}.graphml"
        }
    )
