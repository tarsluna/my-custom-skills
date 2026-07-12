# Schéma `data.csv`

Une ligne par ad analysée. Toutes les colonnes sont obligatoires (vide accepté si non disponible).

## Colonnes

| # | Colonne | Type | Description |
|---|---|---|---|
| 1 | `concurrent` | string | Nom de la marque |
| 2 | `page_id` | string | ID Meta de la page concurrente |
| 3 | `ad_id` | string | ID Meta de l'ad |
| 4 | `format` | enum | `FaceCam` / `UGC` / `Static` / `Carousel` / `VSL` / `Other` |
| 5 | `angle` | enum | `Douleur` / `Désir` / `Preuve` / `ContreIntuitif` / `Urgence` |
| 6 | `hook` | string | Verbatim des 3 premières secondes ou première phrase |
| 7 | `primary_text` | string | Texte primaire complet de l'ad |
| 8 | `headline` | string | Headline (si Lead Form ou conversion) |
| 9 | `cta` | string | Bouton CTA (Sign Up, Learn More, etc.) |
| 10 | `start_date` | date | Date de début de diffusion (ISO) |
| 11 | `last_seen` | date | Dernière date de diffusion observée |
| 12 | `days_active` | int | Nombre de jours d'activité (last_seen - start_date) |
| 13 | `winner` | bool | `true` si days_active > 21 |
| 14 | `hero` | bool | `true` si days_active > 60 |
| 15 | `evergreen` | bool | `true` si days_active > 180 |
| 16 | `countries` | string | Pays de diffusion (comma separated) |
| 17 | `platforms` | string | `facebook,instagram,messenger,audience_network` |
| 18 | `media_path` | string | Chemin local du fichier média téléchargé |
| 19 | `media_type` | enum | `image` / `video` / `carousel` |
| 20 | `landing_url` | string | URL de destination de l'ad |
| 21 | `notes` | string | Notes libres (variantes A/B détectées, etc.) |

## Exemple de ligne

```csv
concurrent,page_id,ad_id,format,angle,hook,primary_text,headline,cta,start_date,last_seen,days_active,winner,hero,evergreen,countries,platforms,media_path,media_type,landing_url,notes
Closer Evolution,123456,987654,FaceCam,Douleur,"Si t'es closer et que tu plafonnes à 3K","Si t'es closer et que tu plafonnes à 3K par mois, cette vidéo est pour toi...","Passe à 10K en 6 mois",Sign Up,2026-01-15,2026-04-07,82,true,true,false,"FR,BE,CH","facebook,instagram",creatives/closer-evolution/ad-987654.mp4,video,https://closerevolution.com/sl,"Variante A/B avec différents hooks détectée"
```

## Encodage

- UTF-8 sans BOM
- Séparateur : virgule
- Quoting : double quote pour tout champ contenant virgule, retour chariot ou guillemet
- Date format : ISO `YYYY-MM-DD`
