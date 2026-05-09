package configfiles

import (
	"strings"
	"testing"

	"golang.org/x/text/encoding/charmap"
)

func TestDecodeFileFallsBackToWindows1251(t *testing.T) {
	encoded, err := charmap.Windows1251.NewEncoder().Bytes([]byte("Цилиндрический\n1\n2"))
	if err != nil {
		t.Fatalf("encode cp1251: %v", err)
	}

	decoded, err := DecodeFile(encoded)
	if err != nil {
		t.Fatalf("decode file: %v", err)
	}

	if !strings.HasPrefix(decoded, "Цилиндрический") {
		t.Fatalf("expected decoded robot type, got %q", decoded)
	}
}

func TestParseMapsRussianRobotTypeToFrontendKey(t *testing.T) {
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

	config := Parse(strings.Join(lines, "\n"))
	state := ToFrontendState(config)

	if state["robotType"] != "cylindrical" {
		t.Fatalf("expected cylindrical, got %#v", state["robotType"])
	}
}
