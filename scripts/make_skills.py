"""Render the skills list below to assets/skills-v1.svg (one local image, no per-badge requests) and point README at it."""
import re
import urllib.request

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
        ("Azure", "0078D4", "microsoftazure"), ("AWS", "FF9900", "amazonaws"), ("GCP", "4285F4", "googlecloud"),
        ("OVHcloud", "123F6D", "ovh"), ("Oracle Cloud", "F80000", "oracle"), ("Huawei Cloud", "CF0A2C", "huawei"),
        ("EKS", "FF9900", "amazonaws"), ("AKS", "0078D4", "microsoftazure"), ("S3", "569A31", "amazons3"), 
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

OUT = "assets/skills-v1.svg"
WIDTH = 860
BADGE_H, GAP, ROW_GAP, PAD_X = 20, 4, 5, 8
ICON = 12
FONT = "Verdana,'DejaVu Sans',Geneva,sans-serif"

_paths = {}


def icon_path(slug):
    """SVG path data of a simple-icons logo (24x24 viewBox), or None when no release has it."""
    if slug not in _paths:
        _paths[slug] = None
        for v in ("11.0.0", "9.21.0", "latest"):
            try:
                svg = urllib.request.urlopen(f"https://cdn.jsdelivr.net/npm/simple-icons@{v}/icons/{slug}.svg", timeout=30).read().decode()
            except Exception:
                continue
            m = re.search(r'<path d="([^"]+)"', svg)
            if m:
                _paths[slug] = m.group(1)
                break
        if _paths[slug] is None:
            print(f"  no icon for {slug}")
    return _paths[slug]


def text_width(text):
    try:
        from PIL import ImageFont
        return ImageFont.truetype("C:/Windows/Fonts/verdana.ttf", 11).getlength(text)
    except Exception:
        return len(text) * 6.4


def is_light(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.62


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(items):
    """Greedy-wrap badges into rows no wider than WIDTH; each badge is (label, color, path, width, text_width)."""
    badges = []
    for label, color, slug in items:
        path = icon_path(slug) if slug else None
        tw = text_width(label)
        w = PAD_X * 2 + tw + (ICON + 5 if path else 0)
        badges.append((label, color, path, w, tw))
    rows, cur, cur_w = [], [], 0
    for b in badges:
        add = b[3] + (GAP if cur else 0)
        if cur and cur_w + add > WIDTH - 20:
            rows.append((cur, cur_w))
            cur, cur_w, add = [], 0, b[3]
        cur.append(b)
        cur_w += add
    if cur:
        rows.append((cur, cur_w))
    return rows


def build_svg():
    y = 8
    parts = []
    for cat, items in SKILLS.items():
        parts.append(f'<text class="t" x="{WIDTH / 2}" y="{y + 13}" text-anchor="middle" font-size="13" font-weight="700">{esc(cat)}</text>')
        y += 24
        for row, row_w in layout(items):
            x = (WIDTH - row_w) / 2
            for label, color, path, w, tw in row:
                fg = "#1f2328" if is_light(color) else "#ffffff"
                parts.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{BADGE_H}" rx="3" fill="#{color}"/>')
                tx = x + PAD_X
                if path:
                    s = ICON / 24
                    parts.append(f'<path transform="translate({x + PAD_X:.1f} {y + (BADGE_H - ICON) / 2}) scale({s:.4f})" d="{path}" fill="{fg}"/>')
                    tx += ICON + 5
                parts.append(f'<text x="{tx:.1f}" y="{y + 14}" font-size="11" fill="{fg}" textLength="{tw:.1f}" lengthAdjust="spacingAndGlyphs">{esc(label)}</text>')
                x += w + GAP
            y += BADGE_H + ROW_GAP
        y += 12
    css = (f"text{{font-family:{FONT}}}.t{{fill:#e6edf3}}"
           "@media (prefers-color-scheme:light){.t{fill:#1f2328}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{y}" viewBox="0 0 {WIDTH} {y}" role="img" '
            f'aria-label="Skills">'
            f'<style>{css}</style>{"".join(parts)}</svg>')


if __name__ == "__main__":
    svg = build_svg()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    alt = "Skills: " + "; ".join(f"{c}: " + ", ".join(i[0] for i in items) for c, items in SKILLS.items())
    s = open("README.md", encoding="utf-8").read()
    new = f'<!-- SKILLS:START -->\n<img src="{OUT}" alt="{alt}" width="100%"/>\n<!-- SKILLS:END -->'
    s = re.sub(r"<!-- SKILLS:START -->.*<!-- SKILLS:END -->", lambda m: new, s, flags=re.S)
    open("README.md", "w", encoding="utf-8").write(s)
    print(f"wrote {OUT} ({len(svg) // 1024} KB)")
