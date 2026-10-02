"""Rebuild the skills section of README.md (between the SKILLS markers) from the list below."""
import base64
import re
import urllib.request

# Icons shields.io no longer ships: fetched from an older simple-icons release and embedded.
EMBED = {"microsoftazure", "amazonaws", "oracle", "amazons3", "tableau", "powerbi", "openai",
         "microsoftteams", "microsoftsharepoint", "microsoftoffice", "powerautomate", "sonarqube", "microsoft"}

# (label, hex colour, icon slug or None)
SKILLS = {
    "Team & Project Management": [
        ("Jira", "0052CC", "jira"), ("Confluence", "172B4D", "confluence"), ("Notion", "000000", "notion"),
        ("Trello", "0052CC", "trello"), ("Agile", "6e5494", None), ("Scrum", "6e5494", None),
        ("Kanban", "6e5494", None), ("Sprint Planning", "6e5494", None), ("Team Leadership", "6e5494", None),
        ("KPI", "6e5494", None), ("SLA", "6e5494", None), ("Backlog", "6e5494", None),
        ("Incident & Priority Management", "6e5494", None), ("IT Governance", "6e5494", None),
    ],
    "Infrastructure & DevOps": [
        ("Docker", "2496ED", "docker"), ("Kubernetes", "326CE5", "kubernetes"), ("Helm", "0F1689", "helm"),
        ("Terraform", "7B42BC", "terraform"), ("Ansible", "EE0000", "ansible"), ("IaC", "5C4EE5", "terraform"),
        ("Bash", "4EAA25", "gnubash"), ("Shell Scripting", "4EAA25", "gnubash"), ("YAML", "CB171E", "yaml"),
        ("Cron Jobs", "555555", None), ("GitLab CI", "FC6D26", "gitlab"), ("CI/CD", "2088FF", "githubactions"),
        ("Git", "F05032", "git"), ("GitHub", "181717", "github"), ("GitLab", "FC6D26", "gitlab"),
        ("Bitbucket", "0052CC", "bitbucket"), ("Code Review", "555555", None), ("Merge Requests", "555555", None),
        ("Branch Management", "555555", None), ("Blue-Green", "2E7D32", None), ("Canary", "F9A825", None),
        ("Staging Releases", "555555", None), ("Rollback Strategies", "555555", None),
    ],
    "Cloud & Systems": [
        ("Azure", "0078D4", "microsoftazure"), ("GCP", "4285F4", "googlecloud"),
        ("OVHcloud", "123F6D", "ovh"), ("Oracle Cloud", "F80000", "oracle"), ("Huawei Cloud", "CF0A2C", "huawei"),
        ("AKS", "0078D4", "microsoftazure"), 
        ("Linux", "FCC624", "linux"), ("Sovereign Cloud", "0A66C2", None), ("Multi-cloud", "0A66C2", None),
        ("Cloud Architecture", "0A66C2", None), ("Capacity Planning", "0A66C2", None),
    ],
    "Networking & Security": [
        ("Nginx", "009639", "nginx"), ("Traefik", "24A1C1", "traefikproxy"), ("Load Balancing", "555555", None),
        ("VPN", "EA7E20", "openvpn"), ("Firewall", "B71C1C", None), ("DNS", "555555", None),
        ("SSL/TLS", "003A70", "letsencrypt"), ("Zero Trust", "B71C1C", None), ("OAuth 2.0", "EB5424", None),
        ("RBAC", "B71C1C", None), ("IAM", "B71C1C", None), ("Active Directory", "0078D4", "microsoft"),
        ("GPO", "0078D4", None), ("Keycloak", "4D4D4D", "keycloak"), ("HashiCorp Vault", "FFEC6E", "vault"),
        ("Secrets Management", "B71C1C", None),
    ],
    "Monitoring & Observability": [
        ("Prometheus", "E6522C", "prometheus"), ("Grafana", "F46800", "grafana"), ("Tempo", "F46800", "grafana"),
        ("Elasticsearch", "005571", "elasticsearch"), ("Logstash", "005571", "logstash"),
        ("Kibana", "005571", "kibana"), ("OpenTelemetry", "425CC7", "opentelemetry"),
        ("Splunk", "000000", "splunk"), ("Zabbix", "CC0000", None), ("Nagios", "1B1B1B", None),
        ("Shinken", "6c8e3b", None), ("Netdata", "00AB44", "netdata"), ("SLI / SLO", "555555", None),
        ("Error Tracking", "555555", None), ("Health Checks", "555555", None),
    ],
    "Data & KPI Reporting": [
        ("Odoo", "714B67", "odoo"), ("SAP", "0FAAFF", "sap"), ("GLPI", "33658A", None),
        ("PostgreSQL", "4169E1", "postgresql"), ("MySQL", "4479A1", "mysql"), ("MongoDB", "47A248", "mongodb"),
        ("MariaDB", "003545", "mariadb"), ("Supabase", "3FCF8E", "supabase"), ("Firebase", "FFCA28", "firebase"),
        ("Redis", "DC382D", "redis"), ("Kafka", "231F20", "apachekafka"), ("Celery", "37814A", "celery"),
        ("ETL Pipelines", "555555", None), ("Superset", "20A6C9", "apachesuperset"), ("Tableau", "E97627", "tableau"),
        ("Power BI", "F2C811", "powerbi"), ("Snowflake", "29B5E8", "snowflake"), ("Databricks", "FF3621", "databricks"),
        ("Data Visualization", "555555", None), ("Reporting Automation", "555555", None),
    ],
    "Automation, APIs & AI": [
        ("Python", "3776AB", "python"), ("FastAPI", "009688", "fastapi"), ("Node.js", "339933", "nodedotjs"),
        ("TypeScript", "3178C6", "typescript"), ("REST API", "009688", None), ("GraphQL", "E10098", "graphql"),
        ("Swagger", "85EA2D", "swagger"), ("Postman", "FF6C37", "postman"), ("Web Scraping", "555555", None),
        ("OpenAI API", "412991", "openai"), ("Anthropic API", "D97757", "anthropic"),
        ("Chrome API", "4285F4", "googlechrome"), ("LangChain", "1C3C3C", "langchain"),
        ("LangGraph", "1C3C3C", "langchain"), ("Hugging Face", "FFD21E", "huggingface"), ("Ollama", "000000", "ollama"),
        ("ChromaDB", "FF6446", None), ("RAG", "6e5494", None), ("Fine Tuning", "6e5494", None),
        ("Prompt Engineering", "6e5494", None), ("Agentic AI", "6e5494", None), ("MLOps", "6e5494", None),
        ("NLP", "6e5494", None), ("LLMs", "6e5494", None), ("Copilot Studio", "0078D4", "microsoft"),
        ("Power Automate", "0066FF", "powerautomate"), ("n8n", "EA4B71", "n8n"), ("Zapier", "FF4F00", "zapier"),
        ("Microsoft 365", "D83B01", "microsoftoffice"), ("SharePoint", "0078D4", "microsoftsharepoint"),
        ("Teams", "6264A7", "microsoftteams"), ("WhatsApp", "25D366", "whatsapp"),
    ],
    "Soft Skills": [
        (s, "30363d", None) for s in (
            "Problem Solving", "Critical Thinking", "Decision Making", "Adaptability", "Fast Learning",
            "Attention to Detail", "Empathy", "Active Listening", "Conflict Resolution", "Emotional Intelligence")
    ],
}

_cache = {}


def icon_data(slug):
    if slug not in _cache:
        for v in ("11.0.0", "9.21.0"):
            try:
                svg = urllib.request.urlopen(f"https://cdn.jsdelivr.net/npm/simple-icons@{v}/icons/{slug}.svg", timeout=30).read()
                break
            except Exception:
                continue
        else:
            raise SystemExit(f"icon not found: {slug}")
        svg = svg.replace(b"<svg ", b'<svg fill="white" ', 1)
        _cache[slug] = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
    return _cache[slug]


def badge(label, color, slug):
    text = label.replace("-", "--").replace("_", "__").replace(" ", "_").replace("/", "%2F").replace("&", "%26")
    url = f"https://img.shields.io/badge/-{text}-{color}?style=flat-square"
    if slug:
        logo = icon_data(slug) if slug in EMBED else slug
        url += f"&logo={logo}&logoColor=white"
    return f"![{label}]({url})"


def build():
    parts = []
    for cat, items in SKILLS.items():
        parts.append(f"**{cat}**<br/>\n" + "\n".join(badge(*i) for i in items))
    return "\n\n".join(parts)


if __name__ == "__main__":
    s = open("README.md", encoding="utf-8").read()
    new = f"<!-- SKILLS:START -->\n{build()}\n<!-- SKILLS:END -->"
    if "<!-- SKILLS:START -->" in s:
        s = re.sub(r"<!-- SKILLS:START -->.*<!-- SKILLS:END -->", lambda m: new, s, flags=re.S)
    else:
        a = s.index("**Infrastructure & DevOps**")
        b = s.index("<br/>\n\n<em>Let's connect")
        s = s[:a] + new + "\n\n" + s[b:]
    open("README.md", "w", encoding="utf-8").write(s)
    print("skills section updated")
