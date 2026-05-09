package main

import (
	"bytes"
	"encoding/json"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"golang.org/x/text/encoding/charmap"
)

func TestUploadConfigFileDecodesWindows1251RobotType(t *testing.T) {
	var body bytes.Buffer
	writer := multipart.NewWriter(&body)
	part, err := writer.CreateFormFile("file", "robot_config.txt")
	if err != nil {
		t.Fatalf("create form file: %v", err)
	}

	lines := []string{"Цилиндрический"}
	for i := 0; i < 78; i++ {
		lines = append(lines, "0")
	}
	lines[61] = "1,1"
	lines[62] = "0.002,0.002"
	lines[63] = "24,24"
	lines[64] = "1,1"
	lines[65] = "1,1"
	lines[66] = "1,1"
	lines[67] = "1,1"
	lines[68] = "0,0,0,0"
	lines[69] = "0,0,0,0"
	lines[70] = "0,0,0,0"
	lines[71] = "0,0,0,0,0,0,0,0,0"
	lines[72] = "0,0,0,0,0,0,0,0,0"
	lines[73] = "0,0,0,0,0,0,0,0,0"
	lines[74] = "0,0,0,0,0,0,0,0,0"
	lines[75] = "0,0,0,0,0,0,0,0,0"
	lines[76] = "line"
	lines[77] = "0,0,0,0,0"
	lines = append(lines, "0,0,0,0")

	encoded, err := charmap.Windows1251.NewEncoder().Bytes([]byte(strings.Join(lines, "\n")))
	if err != nil {
		t.Fatalf("encode cp1251: %v", err)
	}
	if _, err := part.Write(encoded); err != nil {
		t.Fatalf("write multipart body: %v", err)
	}
	if err := writer.Close(); err != nil {
		t.Fatalf("close multipart writer: %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "/api/data/upload", &body)
	req.Header.Set("Content-Type", writer.FormDataContentType())
	rec := httptest.NewRecorder()

	uploadConfigFile(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	var payload map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &payload); err != nil {
		t.Fatalf("unmarshal response: %v", err)
	}
	state := payload["state"].(map[string]any)
	if state["robotType"] != "cylindrical" {
		t.Fatalf("expected cylindrical robotType, got %#v", state["robotType"])
	}
}

func TestDownloadConfigFileReturnsWindows1251Attachment(t *testing.T) {
	requestBody := `{"robotType":"cylindrical","motorParams":{"J":[1,1],"Te":[0.002,0.002],"Umax":[24,24],"Fi":[1,1],"Ce":[1,1],"Ra":[1,1],"Cm":[1,1]}}`
	req := httptest.NewRequest(http.MethodPost, "/api/data/download", strings.NewReader(requestBody))
	rec := httptest.NewRecorder()

	downloadConfigFile(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}
	if got := rec.Header().Get("Content-Type"); !strings.Contains(got, "windows-1251") {
		t.Fatalf("expected windows-1251 content type, got %q", got)
	}
	if got := rec.Header().Get("Content-Disposition"); !strings.Contains(got, "robot_config.txt") {
		t.Fatalf("expected attachment filename, got %q", got)
	}

	decoded, err := charmap.Windows1251.NewDecoder().String(rec.Body.String())
	if err != nil {
		t.Fatalf("decode response body: %v", err)
	}
	if !strings.Contains(decoded, "Цилиндрический") {
		t.Fatalf("expected cylindrical robot type in file, got %q", decoded)
	}
}
