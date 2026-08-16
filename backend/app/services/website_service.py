import os, json, logging, time
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR.parent / "data"
WEBSITES_DIR = DATA_DIR / "websites"
WEBSITES_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000").rstrip("/")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _atomic_write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)
# ============================================
# BANCO DE IMÁGENES POR INDUSTRIA (Unsplash - GRATIS y HD)
# ============================================
INDUSTRY_IMAGES = {
    "pasteleria": {
        "hero": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1558301211-0d8c8ddee6ec?w=600&q=80",
            "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=600&q=80",
            "https://images.unsplash.com/photo-1535141192574-577bf8821c5f?w=600&q=80",
            "https://images.unsplash.com/photo-1562440499-64c9a111f713?w=600&q=80",
            "https://images.unsplash.com/photo-1587668178277-295251f900ce?w=600&q=80",
            "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=600&q=80",
            "https://images.unsplash.com/photo-1542826435-b99d325e0c48?w=600&q=80",
            "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=600&q=80"
        ]
    },
    "reposteria": {
        "hero": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1558301211-0d8c8ddee6ec?w=600&q=80",
            "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=600&q=80",
            "https://images.unsplash.com/photo-1535141192574-577bf8821c5f?w=600&q=80",
            "https://images.unsplash.com/photo-1562440499-64c9a111f713?w=600&q=80",
            "https://images.unsplash.com/photo-1587668178277-295251f900ce?w=600&q=80",
            "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=600&q=80",
            "https://images.unsplash.com/photo-1542826435-b99d325e0c48?w=600&q=80",
            "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=600&q=80"
        ]
    },
    "panaderia": {
        "hero": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1549931319-a545dcf303c8?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&q=80",
            "https://images.unsplash.com/photo-1549931319-a545dcf303c8?w=600&q=80",
            "https://images.unsplash.com/photo-1568254183919-78a4f43a2877?w=600&q=80",
            "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600&q=80",
            "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=600&q=80",
            "https://images.unsplash.com/photo-1517686469429-8bdb88b9f907?w=600&q=80",
            "https://images.unsplash.com/photo-1574085733530-9c8a7c0b5c6e?w=600&q=80",
            "https://images.unsplash.com/photo-1598373182133-52452f7691ef?w=600&q=80"
        ]
    },
    "restaurante": {
        "hero": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1504642723647-d623a4006d02?w=600&q=80",
            "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&q=80",
            "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=600&q=80",
            "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80",
            "https://images.unsplash.com/photo-1551218808-94e220e084d2?w=600&q=80",
            "https://images.unsplash.com/photo-1559847844-5315695dadae?w=600&q=80",
            "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&q=80",
            "https://images.unsplash.com/photo-1424847651672-bf20a4b0982b?w=600&q=80"
        ]
    },
    "cafeteria": {
        "hero": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1445116572660-236099ec97a0?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=600&q=80",
            "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&q=80",
            "https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=600&q=80",
            "https://images.unsplash.com/photo-1507139836480-9ea980f8e862?w=600&q=80",
            "https://images.unsplash.com/photo-1511926627908-9a3c9b287307?w=600&q=80",
            "https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=600&q=80",
            "https://images.unsplash.com/photo-1559496417-e7f25cb247f3?w=600&q=80",
            "https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=600&q=80"
        ]
    },
    "tecnologia": {
        "hero": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&q=80",
            "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=600&q=80",
            "https://images.unsplash.com/photo-1551434678-e076c223a692?w=600&q=80",
            "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&q=80",
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80",
            "https://images.unsplash.com/photo-1531233558888-9c4f3c5c4c5f?w=600&q=80"
        ]
    },
    "software": {
        "hero": "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=600&q=80",
            "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&q=80",
            "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=600&q=80",
            "https://images.unsplash.com/photo-1551434678-e076c223a692?w=600&q=80",
            "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&q=80",
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80"
        ]
    },
    "consultoria": {
        "hero": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1600880292089-90a7e086ee0c?w=600&q=80",
            "https://images.unsplash.com/photo-1507672561168-30d1d1c079c6?w=600&q=80",
            "https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=600&q=80",
            "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&q=80",
            "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=600&q=80"
        ]
    },
    "gimnasio": {
        "hero": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600&q=80",
            "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=600&q=80",
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=600&q=80",
            "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=600&q=80",
            "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=600&q=80",
            "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=600&q=80",
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600&q=80",
            "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=600&q=80"
        ]
    },
    "fitness": {
        "hero": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=600&q=80",
            "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=600&q=80",
            "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600&q=80",
            "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=600&q=80",
            "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=600&q=80",
            "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=600&q=80",
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600&q=80",
            "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=600&q=80"
        ]
    },
    "clinica": {
        "hero": "https://images.unsplash.com/photo-1519494123728-cf00c82424b5?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1631815583675-b20c6c30b455?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1519491050282-cf00c82424b5?w=600&q=80",
            "https://images.unsplash.com/photo-1551076805-e1869033e5cc?w=600&q=80",
            "https://images.unsplash.com/photo-1584982751601-97dcc096659c?w=600&q=80",
            "https://images.unsplash.com/photo-1631815583675-b20c6c30b455?w=600&q=80",
            "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600&q=80",
            "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=600&q=80",
            "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600&q=80",
            "https://images.unsplash.com/photo-1629909613654-28e377c36b09?w=600&q=80"
        ]
    },
    "medico": {
        "hero": "https://images.unsplash.com/photo-1551076805-e1869033e5cc?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1631815583675-b20c6c30b455?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1551076805-e1869033e5cc?w=600&q=80",
            "https://images.unsplash.com/photo-1584982751601-97dcc096659c?w=600&q=80",
            "https://images.unsplash.com/photo-1631815583675-b20c6c30b455?w=600&q=80",
            "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600&q=80",
            "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=600&q=80",
            "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600&q=80",
            "https://images.unsplash.com/photo-1629909613654-28e377c36b09?w=600&q=80",
            "https://images.unsplash.com/photo-1519494123728-cf00c82424b5?w=600&q=80"
        ]
    },
    "dental": {
        "hero": "https://images.unsplash.com/photo-1606811971618-4486d14f3f99?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1606811971618-4486d14f3f99?w=600&q=80",
            "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=600&q=80",
            "https://images.unsplash.com/photo-1609840114035-3c981b782dfe?w=600&q=80",
            "https://images.unsplash.com/photo-1629909615184-74f495363b67?w=600&q=80",
            "https://images.unsplash.com/photo-1607186073325-5b5c4f8c4e2d?w=600&q=80",
            "https://images.unsplash.com/photo-1598256989800-fe51e5b9ce5b?w=600&q=80",
            "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=600&q=80",
            "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=600&q=80"
        ]
    },
    "estetica": {
        "hero": "https://images.unsplash.com/photo-1560750588-26465e851f1d?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1560750588-26465e851f1d?w=600&q=80",
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=600&q=80",
            "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=600&q=80",
            "https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?w=600&q=80",
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600&q=80",
            "https://images.unsplash.com/photo-1519415510236-718bdfcd89c8?w=600&q=80",
            "https://images.unsplash.com/photo-1515377986180-949c05f3c5d5?w=600&q=80",
            "https://images.unsplash.com/photo-1522335789203-aaa2f6fe6b5d?w=600&q=80"
        ]
    },
    "spa": {
        "hero": "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=600&q=80",
            "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=600&q=80",
            "https://images.unsplash.com/photo-1519415510236-718bdfcd89c8?w=600&q=80",
            "https://images.unsplash.com/photo-1515377986180-949c05f3c5d5?w=600&q=80",
            "https://images.unsplash.com/photo-1522335789203-aaa2f6fe6b5d?w=600&q=80",
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=600&q=80",
            "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=600&q=80",
            "https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?w=600&q=80"
        ]
    },
    "fotografia": {
        "hero": "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1554048612-b6a482bc67e5?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=600&q=80",
            "https://images.unsplash.com/photo-1554048612-b6a482bc67e5?w=600&q=80",
            "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=600&q=80",
            "https://images.unsplash.com/photo-1471341971476-ae15ff5dd4ea?w=600&q=80",
            "https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=600&q=80",
            "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=600&q=80",
            "https://images.unsplash.com/photo-1500051638674-ff996a0ec29e?w=600&q=80",
            "https://images.unsplash.com/photo-1506947411487-a56738267384?w=600&q=80"
        ]
    },
    "arquitectura": {
        "hero": "https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=600&q=80",
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600&q=80",
            "https://images.unsplash.com/photo-1486718448742-163732cd1544?w=600&q=80",
            "https://images.unsplash.com/photo-1511870987772-a162da1582cc?w=600&q=80",
            "https://images.unsplash.com/photo-1494526585095-c41746248156?w=600&q=80",
            "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?w=600&q=80",
            "https://images.unsplash.com/photo-1518005020951-eccb494ad742?w=600&q=80",
            "https://images.unsplash.com/photo-1464146072230-91cabc968266?w=600&q=80"
        ]
    },
    "moda": {
        "hero": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80",
            "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=600&q=80",
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80",
            "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80",
            "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80",
            "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600&q=80",
            "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80",
            "https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=600&q=80"
        ]
    },
    "educacion": {
        "hero": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=600&q=80",
            "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=600&q=80",
            "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&q=80",
            "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&q=80",
            "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=600&q=80",
            "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=600&q=80",
            "https://images.unsplash.com/photo-1497486751825-1233686d5d80?w=600&q=80",
            "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=600&q=80"
        ]
    },
    "legal": {
        "hero": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&q=80",
            "https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=600&q=80",
            "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=600&q=80",
            "https://images.unsplash.com/photo-1507652391088-7d7fc0e8f369?w=600&q=80",
            "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600&q=80",
            "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=600&q=80",
            "https://images.unsplash.com/photo-1479142506502-19b3a3b7ff33?w=600&q=80",
            "https://images.unsplash.com/photo-1507038772120-7fff76f79d79?w=600&q=80"
        ]
    },
    "inmobiliaria": {
        "hero": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1560520031-3a4dc4e7de0c?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&q=80",
            "https://images.unsplash.com/photo-1560520031-3a4dc4e7de0c?w=600&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&q=80",
            "https://images.unsplash.com/photo-1494526585095-c41746248156?w=600&q=80",
            "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=600&q=80",
            "https://images.unsplash.com/photo-1560520653-9e0e4c89eb11?w=600&q=80",
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=600&q=80",
            "https://images.unsplash.com/photo-1516156008625-3a9d6067fab5?w=600&q=80"
        ]
    },
    "automotriz": {
        "hero": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=600&q=80",
            "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=600&q=80",
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=600&q=80",
            "https://images.unsplash.com/photo-1542362567-b07e54358753?w=600&q=80",
            "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=600&q=80",
            "https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=600&q=80",
            "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=600&q=80",
            "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=600&q=80"
        ]
    },
    "marketing": {
        "hero": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&q=80",
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=600&q=80",
            "https://images.unsplash.com/photo-1552664196-f549fc812ad9?w=600&q=80",
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&q=80",
            "https://images.unsplash.com/photo-1533750516457-a7f992034fec?w=600&q=80"
        ]
    },
    "default": {
        "hero": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&q=80",
            "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=600&q=80",
            "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=600&q=80",
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&q=80"
        ]
    }
}

ICON_MAPPING = {
    "🎂": "fa-birthday-cake", "🍰": "fa-birthday-cake", "🧁": "fa-birthday-cake",
    "⭐": "fa-star", "🌟": "fa-star", "✨": "fa-star",
    "💼": "fa-briefcase", "🛠️": "fa-tools", "🔧": "fa-wrench",
    "🎨": "fa-palette", "📱": "fa-mobile-alt", "💻": "fa-laptop",
    "🏆": "fa-trophy", "🚀": "fa-rocket", "💡": "fa-lightbulb",
    "📞": "fa-phone", "📧": "fa-envelope", "🏠": "fa-home",
    "🎯": "fa-bullseye", "💰": "fa-dollar-sign", "❤️": "fa-heart"
}


def detect_industry_key(industry: str) -> str:
    """Detecta la categoría de industria para asignar imágenes (versión mejorada con más keywords)"""
    industry_lower = industry.lower()
    industry_normalized = industry_lower.replace("í", "i").replace("é", "e").replace("á", "a").replace("ó", "o").replace("ú", "u")
    
    keywords_map = {
        "pasteleria": ["pastel", "pasteleria", "reposteria", "cake", "bakery", "panaderia", "dulce", "cupcake", "galletas", "postres"],
        "panaderia": ["panaderia", "pan", "bread", "panadero", "baguette", "bolleria"],
        "restaurante": ["restaurante", "comida", "food", "cafe", "bar", "pizzeria", "taqueria", "sushi", "cocina", "gourmet", "bistro"],
        "cafeteria": ["cafeteria", "cafe", "coffee", "barista", "espresso", "latte"],
        "tecnologia": ["tecnologia", "software", "tech", "it", "desarrollo", "app", "web", "programacion", "digital", "informatica", "startup"],
        "software": ["software", "app", "aplicacion", "saas", "plataforma", "sistema"],
        "consultoria": ["consultoria", "consultor", "asesoria", "coaching", "finanzas", "legal", "abogado", "contable", "fiscal", "business"],
        "gimnasio": ["gimnasio", "gym", "crossfit", "pesas", "musculacion"],
        "fitness": ["fitness", "deporte", "entrenamiento", "yoga", "pilates", "cardio", "ejercicio"],
        "clinica": ["clinica", "medico", "doctor", "salud", "hospital", "medicina", "consulta"],
        "medico": ["medico", "doctor", "salud", "hospital", "clinica", "pediatra", "cardiologo"],
        "dental": ["dental", "dentista", "ortodoncia", "dientes", "sonrisa", "oral"],
        "estetica": ["estetica", "belleza", "beauty", "maquillaje", "facial", "tratamiento"],
        "spa": ["spa", "masajes", "relajacion", "wellness", "bienestar", "terapia"],
        "fotografia": ["fotografia", "fotografo", "photo", "camara", "retrato", "boda", "evento"],
        "arquitectura": ["arquitectura", "arquitecto", "diseno", "interiores", "construccion", "edificacion"],
        "moda": ["moda", "ropa", "fashion", "boutique", "vestir", "textil", "diseñador"],
        "educacion": ["educacion", "escuela", "colegio", "academia", "curso", "clase", "universidad", "formacion"],
        "legal": ["legal", "abogado", "leyes", "juridico", "notaria", "bufete", "jurisprudencia"],
        "inmobiliaria": ["inmobiliaria", "bienes raices", "real estate", "casas", "departamentos", "propiedades"],
        "automotriz": ["automotriz", "coches", "carros", "vehiculos", "taller", "mecanica", "auto"],
        "marketing": ["marketing", "publicidad", "digital", "redes sociales", "seo", "branding", "comunicacion"]
    }
    
    for category, keywords in keywords_map.items():
        if any(keyword in industry_normalized for keyword in keywords):
            logger.info(f"🎨 Industria detectada: {category} (de: {industry})")
            return category
    
    logger.info(f"🎨 Industria no reconocida, usando default: {industry}")
    return "default"


# Prompts de imagen para el template de servicios (image.pollinations.ai)
IMAGE_PROMPTS = {
    "restaurante": {"hero": "elegant modern restaurant interior warm lighting professional photo", "secondary": "gourmet food plating closeup professional photography", "services": ["gourmet chef cooking", "wine and dining", "dessert plating", "cafe interior", "fresh ingredients", "event catering"]},
    "cafeteria": {"hero": "cozy specialty coffee shop barista latte art", "secondary": "coffee beans and espresso machine detail", "services": ["barista pouring latte art", "iced coffee drinks", "cozy cafe seating", "pastries display", "espresso machine", "coffee tasting"]},
    "pasteleria": {"hero": "beautiful artisan bakery cake display colorful pastries", "secondary": "decorated layer cake closeup", "services": ["birthday cake design", "cupcakes assortment", "wedding cake", "artisan bread", "cookies baking", "sweet desserts"]},
    "panaderia": {"hero": "artisan bakery fresh bread rustic display", "secondary": "fresh baguettes and sourdough", "services": ["sourdough bread", "baguettes", "brioche pastries", "bakery oven", "sandwich making", "baked goods"]},
    "tecnologia": {"hero": "futuristic technology innovation software development abstract", "secondary": "developer workspace multiple screens code", "services": ["mobile app development", "cloud infrastructure", "data analytics", "cybersecurity", "ai solutions", "devops pipeline"]},
    "software": {"hero": "modern software development team agile workspace", "secondary": "code on screen closeup", "services": ["custom software", "saas platform", "api integration", "quality assurance", "product design", "cloud hosting"]},
    "consultoria": {"hero": "professional business consulting meeting strategy boardroom", "secondary": "business charts and growth analysis", "services": ["strategy consulting", "financial planning", "market research", "process optimization", "business coaching", "risk management"]},
    "gimnasio": {"hero": "modern gym equipment weights training atmosphere", "secondary": "athlete training dumbbells", "services": ["personal training", "crossfit classes", "strength training", "nutrition coaching", "cardio zone", "group workouts"]},
    "fitness": {"hero": "fitness yoga wellness active lifestyle", "secondary": "yoga class calm studio", "services": ["yoga classes", "pilates sessions", "cardio training", "personal coaching", "wellness retreat", "stretching routines"]},
    "clinica": {"hero": "modern medical clinic clean professional healthcare", "secondary": "doctor consultation stethoscope", "services": ["general medicine", "specialist consultation", "diagnostics", "vaccination", "patient care", "emergency care"]},
    "medico": {"hero": "professional doctor modern hospital technology", "secondary": "medical equipment diagnostic", "services": ["family medicine", "cardiology", "pediatrics", "lab analysis", "preventive care", "surgical care"]},
    "dental": {"hero": "modern dental clinic bright clean smile", "secondary": "dentist tools professional", "services": ["general dentistry", "orthodontics", "teeth whitening", "implants", "pediatric dental", "emergency dental"]},
    "estetica": {"hero": "luxury beauty salon skincare treatment", "secondary": "facial treatment professional spa", "services": ["facial treatments", "makeup artistry", "skincare routines", "manicure pedicure", "hair styling", "body treatments"]},
    "spa": {"hero": "relaxing spa massage candles tranquility", "secondary": "spa stones towels aromatherapy", "services": ["massage therapy", "aromatherapy", "facial rituals", "hot stone therapy", "wellness packages", "couples spa"]},
    "fotografia": {"hero": "professional photographer studio camera lighting", "secondary": "photography camera lens detail", "services": ["wedding photography", "portrait sessions", "event coverage", "product photography", "corporate shoots", "drone footage"]},
    "arquitectura": {"hero": "modern architecture building design minimal", "secondary": "architect blueprints and models", "services": ["architectural design", "interior design", "construction planning", "renovation projects", "landscape design", "3d rendering"]},
    "moda": {"hero": "fashion boutique clothing collection stylish", "secondary": "tailor sewing fashion detail", "services": ["fashion design", "custom tailoring", "wardrobe styling", "fashion consultation", "boutique curation", "bridal wear"]},
    "educacion": {"hero": "modern classroom learning students education", "secondary": "books and study materials", "services": ["academic courses", "online learning", "tutoring", "workshops", "language classes", "career training"]},
    "legal": {"hero": "law office professional legal counsel", "secondary": "law books and gavel", "services": ["legal consultation", "contracts review", "corporate law", "litigation support", "notary services", "family law"]},
    "inmobiliaria": {"hero": "modern luxury home real estate exterior", "secondary": "keys and house model", "services": ["property sales", "property rentals", "property management", "appraisals", "investment advice", "relocation services"]},
    "automotriz": {"hero": "modern car dealership vehicles showroom", "secondary": "car engine mechanics detail", "services": ["vehicle sales", "maintenance", "bodywork repair", "detailing", "diagnostics", "parts supply"]},
    "marketing": {"hero": "digital marketing strategy social media growth", "secondary": "analytics dashboard marketing metrics", "services": ["social media management", "seo optimization", "paid advertising", "content creation", "branding design", "email marketing"]},
    "default": {"hero": "professional modern business success teamwork", "secondary": "business meeting collaboration office", "services": ["expert consulting", "quality service", "customer support", "innovative solutions", "team work", "guaranteed results"]},
}


def build_service_image_data(industry_key: str) -> dict:
    """Devuelve keywords de imagen para el template de servicios"""
    prompts = IMAGE_PROMPTS.get(industry_key, IMAGE_PROMPTS["default"])
    return {
        "hero": prompts["hero"],
        "secondary": prompts["secondary"],
        "services": list(prompts["services"]),
    }


def map_icons(services: list) -> list:
    for service in services:
        original_icon = service.get("icon", "⭐")
        if str(original_icon).startswith("fa-"):
            continue
        service["icon"] = ICON_MAPPING.get(original_icon, "fa-star")
    return services


class WebsiteService:
    def __init__(self):
        self.llm_service = LLMService()

    def _save_tenant_info(self, tenant_id: str, package: str, deliverables: list):
        tenants_file = DATA_DIR / "tenants.json"
        tenants = []
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                try:
                    tenants = json.load(f)
                except:
                    tenants = []
        existing_idx = next(
            (i for i, t in enumerate(tenants)
             if t.get("id") == tenant_id or t.get("tenant_id") == tenant_id),
            None
        )
        if existing_idx is not None:
            tenants[existing_idx]["package"] = package
            tenants[existing_idx]["deliverables"] = deliverables
            tenants[existing_idx]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Tenant {tenant_id} actualizado")
        else:
            new_tenant = {
                "id": tenant_id,
                "tenant_id": tenant_id,
                "package": package,
                "deliverables": deliverables,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            tenants.append(new_tenant)
            logger.info(f"Tenant {tenant_id} creado nuevo")
        _atomic_write_json(tenants_file, tenants)

    def _render_site(self, template_name: str, site_data: dict, seo_enabled: bool, chatbot_enabled: bool) -> str:
        dummy_request = Request(scope={"type": "http", "method": "GET", "headers": [], "path": "/"})
        industry_key = detect_industry_key(site_data.get("industry", ""))
        images = INDUSTRY_IMAGES.get(industry_key, INDUSTRY_IMAGES["default"])
        site_data["seo_enabled"] = seo_enabled
        site_data["chatbot_enabled"] = chatbot_enabled
        site_data["public_url"] = PUBLIC_URL
        site_data["hero_image"] = images["hero"]
        site_data["about_image"] = images["about"]
        site_data["gallery_images"] = images["gallery"]
        site_data["services"] = map_icons(site_data.get("services", []))
        # Variables que necesita el template services.html (sin romper landing.html)
        site_data.setdefault("google_font", "Poppins")
        site_data.setdefault("cta_text", site_data.get("hero_cta") or "Contáctanos ahora")
        img_data = build_service_image_data(industry_key)
        site_data.setdefault("hero_image_keyword", img_data["hero"])
        site_data.setdefault("secondary_image_keyword", img_data["secondary"])
        site_data.setdefault("service_images", img_data["services"][:max(len(site_data.get("services", [])), 1)])
        try:
            save_dir = WEBSITES_DIR / site_data.get("tenant_id", "unknown")
            save_dir.mkdir(exist_ok=True)
            _atomic_write_json(save_dir / "site_data.json", site_data)
        except Exception as e:
            logger.warning(f"No se pudo guardar site_data.json: {e}")
        return templates.get_template(template_name).render(request=dummy_request, **site_data)

    def regenerate_site(self, tenant_id: str, site_data: dict) -> dict:
        try:
            site_data["cache_buster"] = int(time.time())
            template_name = "services.html" if "servicio" in site_data.get("industry", "").lower() else "landing.html"
            html_content = self._render_site(template_name, site_data, seo_enabled=True, chatbot_enabled=True)
            tenant_dir = WEBSITES_DIR / tenant_id
            tenant_dir.mkdir(exist_ok=True)
            with open(tenant_dir / "index.html", "w", encoding="utf-8-sig") as f:
                f.write(html_content)
            logger.info(f"Sitio regenerado para {tenant_id}")
            return {
                "status": "success",
                "preview_url": f"/data/websites/{tenant_id}/index.html?v={site_data['cache_buster']}"
            }
        except Exception as e:
            logger.error(f"Error regenerando sitio: {e}", exc_info=True)
            return {"status": "error", "detail": str(e)}

    async def generate_modular_service(self, tenant_id: str, industry: str, objective: str, audience: str, tone: str, package: str, brand_hex: str = "#2563eb", brand_secondary: str = "#764ba2", visual_style: str = "modern", page_type: str = "landing", calendly_url: str = "", contact_email: str = "", contact_phone: str = "", contact_address: str = "") -> dict:
        logger.info(f"Procesando paquete: {package} para {tenant_id}")
        if package == "chat_only":
            site_data = {"company_name": tenant_id, "hero_subtitle": f"Chatbot IA para {industry}"}
        else:
            site_data = await self.llm_service.generate_website_json(industry, objective, audience, tone, visual_style)
        site_data["tenant_id"] = tenant_id
        site_data["cache_buster"] = int(time.time())
        site_data["industry"] = industry
        site_data["brand_hex"] = brand_hex
        site_data["brand_secondary"] = brand_secondary
        site_data["calendly_url"] = calendly_url
        site_data["contact_email"] = contact_email
        site_data["contact_phone"] = contact_phone
        site_data["contact_address"] = contact_address
        site_data["page_type"] = page_type
        site_data["visual_style"] = visual_style
        # SEO: título, descripción y palabras clave con valores por defecto editables
        site_data.setdefault("seo_title", f"{site_data.get('company_name', tenant_id)} | {industry.title()} | Servicios")
        site_data.setdefault("seo_description", site_data.get("hero_subtitle", f"Servicios profesionales de {industry}"))
        site_data.setdefault("seo_keywords", f"{industry}, {site_data.get('company_name', tenant_id)}, servicios profesionales, {visual_style}")
        deliverables = []
        preview_url = "#"
        try:
            # Determinar template basado en el tipo de página
            if page_type == "services":
                template_name = "services.html"
            elif page_type == "portfolio":
                template_name = "landing.html"
            elif page_type == "blog":
                template_name = "landing.html"
            elif page_type == "ecommerce":
                template_name = "landing.html"
            else:
                template_name = "landing.html" if "servicio" not in industry.lower() else "services.html"
            
            # Aplicar colores según el tema visual
            theme_colors = {
                "moderno": {"primary": "#2563eb", "secondary": "#764ba2"},
                "minimalista": {"primary": "#1f2937", "secondary": "#6b7280"},
                "corporativo": {"primary": "#1e3a8a", "secondary": "#475569"},
                "creativo": {"primary": "#ec4899", "secondary": "#8b5cf6"},
                "natural": {"primary": "#16a34a", "secondary": "#b45309"},
                "elegante": {"primary": "#ca8a04", "secondary": "#171717"}
            }
            
            if visual_style in theme_colors:
                site_data["brand_hex"] = theme_colors[visual_style]["primary"]
                site_data["brand_secondary"] = theme_colors[visual_style]["secondary"]
            
            if package == "full":
                logger.info("Ejecutando: SERVICIO COMPLETO")
                template_name = "services.html" if "servicio" in industry.lower() else "landing.html"
                html_content = self._render_site(template_name, site_data, seo_enabled=True, chatbot_enabled=True)
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "index.html", "w", encoding="utf-8-sig") as f:
                    f.write(html_content)
                seo_data = {
                    "meta_title": f"{site_data.get('company_name', tenant_id)} | {industry}",
                    "meta_description": site_data.get("hero_subtitle", f"Expertos en {industry}"),
                    "primary_keyword": industry.lower(),
                    "secondary_keywords": [f"{industry} profesional", "mejor servicio", "calidad garantizada"],
                    "schema_json_ld": {"@context": "https://schema.org", "@type": "LocalBusiness", "name": site_data.get("company_name", tenant_id)},
                    "seo_recommendations": [
                        "Crea una sección de FAQ.",
                        "Registra tu negocio en Google Business Profile.",
                        "Solicita reseñas a clientes satisfechos."
                    ]
                }
                schema_string = json.dumps(seo_data.get("schema_json_ld", {}), indent=2, ensure_ascii=False)
                seo_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte SEO | {site_data.get('company_name', tenant_id)}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen p-8">
    <div class="max-w-5xl mx-auto">
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h1 class="text-3xl font-bold">Reporte SEO Profesional</h1>
            <p class="text-gray-600">Empresa: {site_data.get('company_name', tenant_id)} | Industria: {industry}</p>
        </div>
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold mb-4">Meta Tags Optimizados</h2>
            <div class="bg-gray-50 p-4 rounded-lg mb-3">
                <p class="text-sm font-semibold">Titulo SEO:</p>
                <p class="text-blue-600 text-lg">{seo_data['meta_title']}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
                <p class="text-sm font-semibold">Meta Description:</p>
                <p class="text-gray-700">{seo_data['meta_description']}</p>
            </div>
        </div>
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold mb-4">Schema Markup (JSON-LD)</h2>
            <pre class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs overflow-x-auto">{schema_string}</pre>
        </div>
        <div class="bg-white rounded-2xl shadow-xl p-8">
            <h2 class="text-2xl font-bold mb-4">Recomendaciones SEO</h2>
            {''.join([f'<div class="flex gap-3 p-4 bg-gray-50 rounded-lg mb-2"><span>✅</span><p>{rec}</p></div>' for rec in seo_data['seo_recommendations']])}
        </div>
    </div>
</body>
</html>"""
                with open(tenant_dir / "seo-report.html", "w", encoding="utf-8-sig") as f:
                    f.write(seo_html)
                preview_url = f"/data/websites/{tenant_id}/index.html?v={site_data['cache_buster']}"
                deliverables = ["Sitio Web Profesional", "Chatbot RAG", "SEO Completo", "Reporte SEO"]
            elif package == "web_chat":
                template_name = "services.html" if "servicio" in industry.lower() else "landing.html"
                html_content = self._render_site(template_name, site_data, seo_enabled=False, chatbot_enabled=True)
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "index.html", "w", encoding="utf-8-sig") as f:
                    f.write(html_content)
                preview_url = f"/data/websites/{tenant_id}/index.html?v={site_data['cache_buster']}"
                deliverables = ["Sitio Web Profesional", "Chatbot RAG"]
            elif package == "chat_only":
                from app.services.chat_config_service import build_widget_snippet
                widget_code = build_widget_snippet(tenant_id, PUBLIC_URL)
                company_label = site_data.get("company_name", tenant_id)
                chat_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Listo | {company_label}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-blue-50 via-white to-purple-50 min-h-screen p-6">
    <div class="max-w-3xl mx-auto">
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white mb-4 shadow-lg">
                <i class="fa-solid fa-comments text-2xl"></i>
            </div>
            <h1 class="text-3xl font-bold text-gray-900">Tu Chatbot esta listo</h1>
            <p class="text-gray-500 mt-2">{company_label} | ID: <code class="bg-gray-100 px-2 py-0.5 rounded">{tenant_id}</code></p>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2"><span class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold">1</span> Copia el codigo</h2>
            <div class="relative">
                <textarea id="codigo" readonly class="w-full h-28 p-4 bg-gray-900 text-green-300 font-mono text-sm rounded-xl border border-gray-700">{widget_code}</textarea>
                <button onclick="copiar()" class="absolute top-3 right-3 bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg font-semibold">Copiar</button>
            </div>
            <div id="copiado" class="hidden mt-2 text-green-600 text-sm font-semibold"><i class="fa-solid fa-check mr-1"></i>Codigo copiado al portapapeles</div>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2"><span class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold">2</span> Pega el codigo en tu pagina</h2>
            <p class="text-gray-600">Pega el codigo justo antes de la etiqueta <code class="bg-gray-100 px-2 py-0.5 rounded text-red-600">&lt;/body&gt;</code> en el HTML de tu sitio web. Guarda y publica los cambios.</p>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2"><span class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold">3</span> Listo</h2>
            <p class="text-gray-600">El boton flotante del chatbot aparecera en la esquina inferior derecha de tu pagina. Pruebalo en la vista previa de la derecha.</p>
        </div>

        <div class="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white shadow-xl">
            <h2 class="text-xl font-bold mb-2">Vista previa en vivo</h2>
            <p class="text-blue-100 mb-4">Abre el chat en la esquina inferior derecha para probar tu asistente ahora mismo.</p>
        </div>
    </div>
    <script>
    function copiar() {{
        var t = document.getElementById('codigo');
        t.select();
        t.setSelectionRange(0, 99999);
        navigator.clipboard.writeText(t.value);
        var aviso = document.getElementById('copiado');
        aviso.classList.remove('hidden');
        setTimeout(function() {{ aviso.classList.add('hidden'); }}, 2500);
    }}
    </script>
    {widget_code}
</body>
</html>"""
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "chatbot-install.html", "w", encoding="utf-8-sig") as f:
                    f.write(chat_html)
                preview_url = f"/data/websites/{tenant_id}/chatbot-install.html"
                deliverables = ["Codigo del Widget de Chatbot", "Pagina de instalacion + vista previa"]
            elif package == "seo_only":
                seo_data = {
                    "meta_title": f"{industry} | Soluciones Profesionales",
                    "meta_description": f"Expertos en {industry}. {objective}.",
                    "primary_keyword": industry.lower(),
                    "secondary_keywords": [f"{industry} profesional", "mejor servicio"],
                    "schema_json_ld": {"@context": "https://schema.org", "@type": "LocalBusiness", "name": industry},
                    "seo_recommendations": ["Crea una FAQ.", "Registra en Google Business.", "Solicita resenas."]
                }
                schema_string = json.dumps(seo_data.get("schema_json_ld", {}), indent=2, ensure_ascii=False)
                seo_html = f"""<!DOCTYPE html><html><head><title>SEO</title><script src="https://cdn.tailwindcss.com"></script></head>
                <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen p-8"><div class="max-w-5xl mx-auto">
                <div class="bg-white rounded-2xl shadow-xl p-8 mb-6"><h1 class="text-3xl font-bold">Reporte SEO</h1></div>
                <div class="bg-white rounded-2xl shadow-xl p-8"><pre class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs">{schema_string}</pre></div>
                </div></body></html>"""
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "seo-report.html", "w", encoding="utf-8-sig") as f:
                    f.write(seo_html)
                preview_url = f"/data/websites/{tenant_id}/seo-report.html"
                deliverables = ["Auditoria SEO", "Meta Tags", "Schema Markup"]
            self._save_tenant_info(tenant_id, package, deliverables)
            logger.info(f"PROCESO EXITOSO: Paquete {package} para {tenant_id}")
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "package": package,
                "deliverables": deliverables,
                "preview_url": preview_url,
                "site_data": site_data
            }
        except Exception as e:
            logger.error(f"FALLO en paquete {package}: {str(e)}", exc_info=True)
            raise Exception(f"Error generando paquete {package}: {str(e)}")

