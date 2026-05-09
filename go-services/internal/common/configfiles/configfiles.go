package configfiles

import (
	"strconv"
	"strings"
	"unicode/utf8"

	"golang.org/x/text/encoding/charmap"
)

var robotTypeMap = map[string]string{
	"cartesian":      "Декартовый",
	"scara":          "Скара",
	"cylindrical":    "Цилиндрический",
	"coler":          "Колер",
	"Декартовый":     "cartesian",
	"Скара":          "scara",
	"Цилиндрический": "cylindrical",
	"Колер":          "coler",
}

func DecodeFile(content []byte) (string, error) {
	if utf8.Valid(content) {
		return string(content), nil
	}
	if text, err := charmap.Windows1251.NewDecoder().String(string(content)); err == nil {
		return text, nil
	}
	return string(content), nil
}

func Parse(content string) map[string]any {
	lines := strings.Split(strings.TrimSpace(content), "\n")
	getLine := func(index int) string {
		if index >= 0 && index < len(lines) {
			return strings.TrimSpace(lines[index])
		}
		return ""
	}
	cfg := map[string]any{}
	cfg["robot_type"] = pickRobotType(getLine(0))

	scalars := []struct {
		Key   string
		Index int
	}{
		{"massd_1", 1}, {"massd_2", 2}, {"massd_3", 3}, {"momentd_1", 4},
		{"x_min", 5}, {"y_min", 6}, {"q_min", 7}, {"z_min", 8},
		{"x_max", 9}, {"y_max", 10}, {"q_max", 11}, {"z_max", 12},
		{"moment_1", 13}, {"moment_2", 14}, {"moment_3", 15}, {"length_1", 16},
		{"length_2", 17}, {"distance", 18}, {"masss_2", 19}, {"masss_3", 20},
		{"q1s_min", 21}, {"q1s_max", 22}, {"q2s_min", 23}, {"q2s_max", 24},
		{"q3s_min", 25}, {"q3s_max", 26}, {"zs_min", 27}, {"zs_max", 28},
		{"momentc_1", 29}, {"momentc_2", 30}, {"momentc_3", 31}, {"lengthc_1", 32},
		{"lengthc_2", 33}, {"distancec", 34}, {"massc_2", 35}, {"massc_3", 36},
		{"q1c_min", 37}, {"q1c_max", 38}, {"a2c_min", 39}, {"a2c_max", 40},
		{"q3c_min", 41}, {"q3c_max", 42}, {"zc_min", 43}, {"zc_max", 44},
		{"momentcol_1", 45}, {"momentcol_2", 46}, {"momentcol_3", 47}, {"lengthcol_1", 48},
		{"lengthcol_2", 49}, {"distancecol", 50}, {"masscol_2", 51}, {"masscol_3", 52},
		{"q1col_min", 53}, {"q1col_max", 54}, {"a2col_min", 55}, {"a2col_max", 56},
		{"q3col_min", 57}, {"q3col_max", 58}, {"zcol_min", 59}, {"zcol_max", 60},
	}
	for _, scalar := range scalars {
		cfg[scalar.Key] = parseFloat(getLine(scalar.Index))
	}

	lists := []struct {
		Key   string
		Index int
	}{
		{"J", 61}, {"T_e", 62}, {"Umax", 63}, {"Fi", 64}, {"Ce", 65}, {"Ra", 66}, {"Cm", 67},
		{"Kp", 68}, {"Ki", 69}, {"Kd", 70}, {"t", 71}, {"q1", 72}, {"q2", 73}, {"q3", 74}, {"q4", 75},
	}
	for _, item := range lists {
		cfg[item.Key] = parseFloatList(getLine(item.Index))
	}
	if len(lines) > 76 {
		cfg["trajectory_type"] = getLine(76)
	}
	if len(lines) > 77 {
		cfg["line_params"] = parseFloatList(getLine(77))
	}
	if len(lines) > 78 {
		cfg["circle_params"] = parseFloatList(getLine(78))
	}
	return cfg
}

func ToFrontendState(config map[string]any) map[string]any {
	robotType, _ := config["robot_type"].(string)
	switch robotType {
	case "Декартовый", "Скара", "Цилиндрический", "Колер":
		if mapped, ok := robotTypeMap[robotType]; ok {
			robotType = mapped
		}
	}
	return map[string]any{
		"robotType":         robotType,
		"cartesianParams":   map[string]any{"mass1": num(config, "massd_1"), "mass2": num(config, "massd_2"), "mass3": num(config, "massd_3"), "moment": num(config, "momentd_1")},
		"cartesianLimits":   map[string]any{"Xmin": num(config, "x_min"), "Xmax": num(config, "x_max"), "Ymin": num(config, "y_min"), "Ymax": num(config, "y_max"), "Zmin": num(config, "z_min"), "Zmax": num(config, "z_max"), "Qmin": num(config, "q_min"), "Qmax": num(config, "q_max")},
		"scaraParams":       map[string]any{"moment1": num(config, "moment_1"), "moment2": num(config, "moment_2"), "moment3": num(config, "moment_3"), "length1": num(config, "length_1"), "length2": num(config, "length_2"), "distance": num(config, "distance"), "mass2": num(config, "masss_2"), "mass3": num(config, "masss_3")},
		"scaraLimits":       map[string]any{"q1Min": num(config, "q1s_min"), "q1Max": num(config, "q1s_max"), "q2Min": num(config, "q2s_min"), "q2Max": num(config, "q2s_max"), "q3Min": num(config, "q3s_min"), "q3Max": num(config, "q3s_max"), "zMin": num(config, "zs_min"), "zMax": num(config, "zs_max")},
		"cylindricalParams": map[string]any{"moment1": num(config, "momentc_1"), "moment2": num(config, "momentc_2"), "moment3": num(config, "momentc_3"), "length1": num(config, "lengthc_1"), "length2": num(config, "lengthc_2"), "distance": num(config, "distancec"), "mass2": num(config, "massc_2"), "mass3": num(config, "massc_3")},
		"cylindricalLimits": map[string]any{"q1Min": num(config, "q1c_min"), "q1Max": num(config, "q1c_max"), "a2Min": num(config, "a2c_min"), "a2Max": num(config, "a2c_max"), "q3Min": num(config, "q3c_min"), "q3Max": num(config, "q3c_max"), "zMin": num(config, "zc_min"), "zMax": num(config, "zc_max")},
		"colerParams":       map[string]any{"moment1": num(config, "momentcol_1"), "moment2": num(config, "momentcol_2"), "moment3": num(config, "momentcol_3"), "length1": num(config, "lengthcol_1"), "length2": num(config, "lengthcol_2"), "distance": num(config, "distancecol"), "mass2": num(config, "masscol_2"), "mass3": num(config, "masscol_3")},
		"colerLimits":       map[string]any{"q1Min": num(config, "q1col_min"), "q1Max": num(config, "q1col_max"), "a2Min": num(config, "a2col_min"), "a2Max": num(config, "a2col_max"), "q3Min": num(config, "q3col_min"), "q3Max": num(config, "q3col_max"), "zMin": num(config, "zcol_min"), "zMax": num(config, "zcol_max")},
		"motorParams":       map[string]any{"J": floats(config, "J"), "Te": floats(config, "T_e"), "Umax": floats(config, "Umax"), "Fi": floats(config, "Fi"), "Ce": floats(config, "Ce"), "Ra": floats(config, "Ra"), "Cm": floats(config, "Cm")},
		"regulatorParams":   map[string]any{"Kp": floats(config, "Kp"), "Ki": floats(config, "Ki"), "Kd": floats(config, "Kd")},
		"cyclegram":         map[string]any{"t": floats(config, "t"), "q1": floats(config, "q1"), "q2": floats(config, "q2"), "q3": floats(config, "q3"), "q4": floats(config, "q4")},
		"trajectory": map[string]any{
			"type": pickString(config, "trajectory_type", "line"),
			"line": map[string]any{
				"x1":    pickSliceValue(config, "line_params", 0),
				"x2":    pickSliceValue(config, "line_params", 1),
				"y1":    pickSliceValue(config, "line_params", 2),
				"y2":    pickSliceValue(config, "line_params", 3),
				"speed": pickSliceValue(config, "line_params", 4),
			},
			"circle": map[string]any{
				"x":      pickSliceValue(config, "circle_params", 0),
				"y":      pickSliceValue(config, "circle_params", 1),
				"radius": pickSliceValue(config, "circle_params", 2),
				"speed":  pickSliceValue(config, "circle_params", 3),
			},
		},
	}
}

func Generate(state map[string]any) string {
	getPath := func(defaultValue any, path ...string) any {
		var current any = state
		for _, key := range path {
			asMap, ok := current.(map[string]any)
			if !ok {
				return defaultValue
			}
			current, ok = asMap[key]
			if !ok || current == nil {
				return defaultValue
			}
		}
		return current
	}

	var lines []string
	robotType := toString(getPath("cartesian", "robotType"))
	if mapped, ok := robotTypeMap[robotType]; ok {
		robotType = mapped
	}
	lines = append(lines, robotType)

	scalars := []any{
		getPath(0, "cartesianParams", "mass1"), getPath(0, "cartesianParams", "mass2"), getPath(0, "cartesianParams", "mass3"), getPath(0, "cartesianParams", "moment"),
		getPath(0, "cartesianLimits", "Xmin"), getPath(0, "cartesianLimits", "Ymin"), getPath(0, "cartesianLimits", "Qmin"), getPath(0, "cartesianLimits", "Zmin"),
		getPath(0, "cartesianLimits", "Xmax"), getPath(0, "cartesianLimits", "Ymax"), getPath(0, "cartesianLimits", "Qmax"), getPath(0, "cartesianLimits", "Zmax"),
		getPath(0, "scaraParams", "moment1"), getPath(0, "scaraParams", "moment2"), getPath(0, "scaraParams", "moment3"), getPath(0, "scaraParams", "length1"),
		getPath(0, "scaraParams", "length2"), getPath(0, "scaraParams", "distance"), getPath(0, "scaraParams", "mass2"), getPath(0, "scaraParams", "mass3"),
		getPath(0, "scaraLimits", "q1Min"), getPath(0, "scaraLimits", "q1Max"), getPath(0, "scaraLimits", "q2Min"), getPath(0, "scaraLimits", "q2Max"),
		getPath(0, "scaraLimits", "q3Min"), getPath(0, "scaraLimits", "q3Max"), getPath(0, "scaraLimits", "zMin"), getPath(0, "scaraLimits", "zMax"),
		getPath(0, "cylindricalParams", "moment1"), getPath(0, "cylindricalParams", "moment2"), getPath(0, "cylindricalParams", "moment3"), getPath(0, "cylindricalParams", "length1"),
		getPath(0, "cylindricalParams", "length2"), getPath(0, "cylindricalParams", "distance"), getPath(0, "cylindricalParams", "mass2"), getPath(0, "cylindricalParams", "mass3"),
		getPath(0, "cylindricalLimits", "q1Min"), getPath(0, "cylindricalLimits", "q1Max"), getPath(0, "cylindricalLimits", "a2Min"), getPath(0, "cylindricalLimits", "a2Max"),
		getPath(0, "cylindricalLimits", "q3Min"), getPath(0, "cylindricalLimits", "q3Max"), getPath(0, "cylindricalLimits", "zMin"), getPath(0, "cylindricalLimits", "zMax"),
		getPath(0, "colerParams", "moment1"), getPath(0, "colerParams", "moment2"), getPath(0, "colerParams", "moment3"), getPath(0, "colerParams", "length1"),
		getPath(0, "colerParams", "length2"), getPath(0, "colerParams", "distance"), getPath(0, "colerParams", "mass2"), getPath(0, "colerParams", "mass3"),
		getPath(0, "colerLimits", "q1Min"), getPath(0, "colerLimits", "q1Max"), getPath(0, "colerLimits", "a2Min"), getPath(0, "colerLimits", "a2Max"),
		getPath(0, "colerLimits", "q3Min"), getPath(0, "colerLimits", "q3Max"), getPath(0, "colerLimits", "zMin"), getPath(0, "colerLimits", "zMax"),
	}
	for _, item := range scalars {
		lines = append(lines, toString(item))
	}

	lists := [][]float64{
		toFloatSlice(getPath([]any{0, 0}, "motorParams", "J")),
		toFloatSlice(getPath([]any{0, 0}, "motorParams", "Te")),
		toFloatSlice(getPath([]any{0, 0}, "motorParams", "Umax")),
		toFloatSlice(getPath([]any{0, 0}, "motorParams", "Fi")),
		toFloatSlice(getPath([]any{0, 0}, "motorParams", "Ce")),
		toFloatSlice(getPath([]any{0, 0}, "motorParams", "Ra")),
		toFloatSlice(getPath([]any{0, 0}, "motorParams", "Cm")),
		toFloatSlice(getPath([]any{0, 0, 0, 0}, "regulatorParams", "Kp")),
		toFloatSlice(getPath([]any{0, 0, 0, 0}, "regulatorParams", "Ki")),
		toFloatSlice(getPath([]any{0, 0, 0, 0}, "regulatorParams", "Kd")),
		toFloatSlice(getPath(make([]any, 9), "cyclegram", "t")),
		toFloatSlice(getPath(make([]any, 9), "cyclegram", "q1")),
		toFloatSlice(getPath(make([]any, 9), "cyclegram", "q2")),
		toFloatSlice(getPath(make([]any, 9), "cyclegram", "q3")),
		toFloatSlice(getPath(make([]any, 9), "cyclegram", "q4")),
	}
	for _, list := range lists {
		lines = append(lines, joinFloatSlice(list))
	}

	lines = append(lines, toString(getPath("line", "trajectory", "type")))
	lines = append(lines, joinFloatSlice([]float64{
		toFloat(getPath(0, "trajectory", "line", "x1")),
		toFloat(getPath(0, "trajectory", "line", "x2")),
		toFloat(getPath(0, "trajectory", "line", "y1")),
		toFloat(getPath(0, "trajectory", "line", "y2")),
		toFloat(getPath(0, "trajectory", "line", "speed")),
	}))
	lines = append(lines, joinFloatSlice([]float64{
		toFloat(getPath(0, "trajectory", "circle", "x")),
		toFloat(getPath(0, "trajectory", "circle", "y")),
		toFloat(getPath(0, "trajectory", "circle", "radius")),
		toFloat(getPath(0, "trajectory", "circle", "speed")),
	}))
	return strings.Join(lines, "\n")
}

func EncodeWindows1251(text string) ([]byte, error) {
	return charmap.Windows1251.NewEncoder().Bytes([]byte(text))
}

func pickRobotType(value string) string {
	if mapped, ok := robotTypeMap[value]; ok {
		return mapped
	}
	return value
}

func parseFloat(value string) float64 {
	number, err := strconv.ParseFloat(strings.TrimSpace(value), 64)
	if err != nil {
		return 0
	}
	return number
}

func parseFloatList(value string) []float64 {
	if strings.TrimSpace(value) == "" {
		return []float64{0, 0}
	}
	parts := strings.Split(value, ",")
	result := make([]float64, 0, len(parts))
	for _, part := range parts {
		result = append(result, parseFloat(part))
	}
	return result
}

func toFloat(value any) float64 {
	switch typed := value.(type) {
	case float64:
		return typed
	case float32:
		return float64(typed)
	case int:
		return float64(typed)
	case int64:
		return float64(typed)
	case string:
		return parseFloat(typed)
	default:
		return 0
	}
}

func toString(value any) string {
	switch typed := value.(type) {
	case string:
		return typed
	case float64:
		return strconv.FormatFloat(typed, 'f', -1, 64)
	case int:
		return strconv.Itoa(typed)
	default:
		return "0"
	}
}

func toFloatSlice(value any) []float64 {
	switch typed := value.(type) {
	case []float64:
		return typed
	case []any:
		result := make([]float64, 0, len(typed))
		for _, item := range typed {
			result = append(result, toFloat(item))
		}
		return result
	default:
		return []float64{0, 0}
	}
}

func joinFloatSlice(values []float64) string {
	parts := make([]string, 0, len(values))
	for _, value := range values {
		parts = append(parts, strconv.FormatFloat(value, 'f', -1, 64))
	}
	return strings.Join(parts, ",")
}

func floats(config map[string]any, key string) []float64 {
	value, ok := config[key]
	if !ok {
		return []float64{}
	}
	if typed, ok := value.([]float64); ok {
		return typed
	}
	return toFloatSlice(value)
}

func num(config map[string]any, key string) float64 {
	return toFloat(config[key])
}

func pickString(config map[string]any, key, fallback string) string {
	if value, ok := config[key].(string); ok && value != "" {
		return value
	}
	return fallback
}

func pickSliceValue(config map[string]any, key string, index int) float64 {
	values := floats(config, key)
	if index >= 0 && index < len(values) {
		return values[index]
	}
	return 0
}
