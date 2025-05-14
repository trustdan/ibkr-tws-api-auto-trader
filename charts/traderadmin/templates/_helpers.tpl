{{/*
Expand the name of the chart.
*/}}
{{- define "traderadmin.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "traderadmin.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "traderadmin.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "traderadmin.labels" -}}
helm.sh/chart: {{ include "traderadmin.chart" . }}
{{ include "traderadmin.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "traderadmin.selectorLabels" -}}
app.kubernetes.io/name: {{ include "traderadmin.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Python Orchestrator specific labels
*/}}
{{- define "pythonOrch.labels" -}}
{{ include "traderadmin.labels" . }}
app.kubernetes.io/component: python-orch
{{- end }}

{{/*
Python Orchestrator selector labels
*/}}
{{- define "pythonOrch.selectorLabels" -}}
{{ include "traderadmin.selectorLabels" . }}
app.kubernetes.io/component: python-orch
{{- end }}

{{/*
Go Scanner specific labels
*/}}
{{- define "goScanner.labels" -}}
{{ include "traderadmin.labels" . }}
app.kubernetes.io/component: go-scanner
{{- end }}

{{/*
Go Scanner selector labels
*/}}
{{- define "goScanner.selectorLabels" -}}
{{ include "traderadmin.selectorLabels" . }}
app.kubernetes.io/component: go-scanner
{{- end }}

{{/*
Redis specific labels
*/}}
{{- define "redis.labels" -}}
{{ include "traderadmin.labels" . }}
app.kubernetes.io/component: redis
{{- end }}

{{/*
Redis selector labels
*/}}
{{- define "redis.selectorLabels" -}}
{{ include "traderadmin.selectorLabels" . }}
app.kubernetes.io/component: redis
{{- end }} 