"""Export HealthTech JSON Schema contracts to an explicit directory."""
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from patent_to_pilot.healthtech import contracts
from patent_to_pilot.healthtech.api import HealthTechAPIConfig, HealthTechDispatchReceipt, HealthTechRequest, HealthTechVisibleSource
from patent_to_pilot.healthtech.engine import DossierInput


def main():
    destination=Path(sys.argv[1]);destination.mkdir(parents=True,exist_ok=True)
    for model in [contracts.DeviceQuery,contracts.PatentCandidate,contracts.EvidenceItem,
                  contracts.AcquisitionEvent,contracts.DossierVersion,contracts.RunManifest,DossierInput,
                  HealthTechVisibleSource,HealthTechAPIConfig,HealthTechRequest,HealthTechDispatchReceipt]:
        path=destination/f"{model.__name__}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
