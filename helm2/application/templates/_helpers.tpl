{{/*
Create deployment name
*/}}
{{- define "deployment.name" -}}
{{- printf "%s-deployment-%s-%s" .Chart.Name .Values.environment .Chart.AppVersion -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "mychart.common_labels" -}}
app: {{ .Chart.Name }}
env: {{ .Values.environment }}
region: {{ .Values.region_short }}
app.kubernetes.io/managed-by: helm
{{- end }}

{{/*
Create gateway name
*/}}
{{- define "gateway.name" -}}
{{- printf "%s-gateway-%s" .Chart.Name .Values.environment -}}
{{- end -}}

{{/*
Returns resources values for replica count limits
*/}}
{{- define "replicaCount.initial" -}}
{{- if eq .Values.environment "ci" -}}
{{- .Values.deployment.replicaCount.ci -}}
{{- else if eq .Values.environment "dev" -}}
{{- .Values.deployment.replicaCount.dev -}}
{{- else if eq .Values.environment "int" -}}
{{- .Values.deployment.replicaCount.int -}}
{{- else if eq .Values.environment "qa" -}}
{{- .Values.deployment.replicaCount.qa -}}
{{- else if eq .Values.environment "prod" -}}
{{- .Values.deployment.replicaCount.prod -}}
{{- else -}}
{{- printf "unsupported-service-environment-%s" .Values.environment -}}
{{- end -}}
{{- end -}}

{{/*
Resource Annotations
*/}}
{{- define "mychart.resource_annotations" -}}
app.tr.com/application-asset-insight-id: "207891"
app.tr.com/resource-author: "RAS_Search_Developers@thomsonreuters.com"
app.tr.com/resource-owner: "TR-RAS-VARS-OPS@thomsonreuters.com"
app.tr.com/vendor: "Thomson Reuters"
app.tr.com/repo: "https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey"
{{- end -}}

{{/*
Returns resources values for replica count max
*/}}
{{- define "replicaCount.max" -}}
{{- if eq .Values.environment "ci" -}}
{{- .Values.hpa.max.ci -}}
{{- else if eq .Values.environment "dev" -}}
{{- .Values.hpa.max.dev -}}
{{- else if eq .Values.environment "int" -}}
{{- .Values.hpa.max.int -}}
{{- else if eq .Values.environment "qa" -}}
{{- .Values.hpa.max.qa -}}
{{- else if eq .Values.environment "prod" -}}
{{- .Values.hpa.max.prod -}}
{{- else -}}
{{- printf "unsupported-service-environment-%s" .Values.environment -}}
{{- end -}}
{{- end -}}

{{/*
Returns resources values for replica count max
*/}}
{{- define "datadog.profiler.enabled" -}}
{{- if eq .Values.environment "ci" -}}
"true"
{{- else if eq .Values.environment "dev" -}}
"false"
{{- else if eq .Values.environment "int" -}}
"false"
{{- else if eq .Values.environment "qa" -}}
"false"
{{- else if eq .Values.environment "prod" -}}
"false"
{{- else -}}
{{- printf "unsupported-service-environment-%s" .Values.environment -}}
{{- end -}}
{{- end -}}





