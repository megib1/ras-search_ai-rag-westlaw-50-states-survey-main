{{/*
Common labels
*/}}
{{- define "mychart.common_labels" -}}
app: {{ .Values.application.name }}
env: {{ .Values.environment }}
region: {{ .Values.region_short }}
app.kubernetes.io/managed-by: helm
{{- end }}

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
Returns right service-account role from values file based on environment
*/}}
{{- define "service-account.role" -}}
{{- if eq .Values.environment "ci" -}}
{{- .Values.service.ci.IamRole -}}
{{- else if eq .Values.environment "dev" -}}
{{- .Values.service.ci.IamRole -}}
{{- else if eq .Values.environment "int" -}}
{{- .Values.service.int.IamRole -}}
{{- else if eq .Values.environment "qa" -}}
{{- .Values.service.qa.IamRole -}}
{{- else if eq .Values.environment "prod" -}}
{{- .Values.service.prod.IamRole -}}
{{- else -}}
{{- printf "unsupported-service-environment-%s" .Values.environment -}}
{{- end -}}
{{- end -}}
