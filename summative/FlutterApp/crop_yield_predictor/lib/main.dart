import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

// ---------------------------------------------------------------------------
// CONFIG: point this at your deployed Render API base URL.
// Example after deploying: "https://crop-yield-predictor.onrender.com"
// For local Android emulator development, use: "http://10.0.2.2:8000"
// ---------------------------------------------------------------------------
const String kApiBaseUrl = "http://10.0.2.2:8000";

const List<String> kCountries = [
  "Angola", "Benin", "Burkina Faso", "Burundi", "Cameroon",
  "Central African Republic", "Chad", "Congo, The Democratic Republic of the",
  "Ethiopia", "Ghana", "Kenya", "Lesotho", "Liberia", "Madagascar", "Malawi",
  "Mali", "Mauritania", "Mozambique", "Niger", "Nigeria", "Rwanda", "Senegal",
  "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan",
  "Tanzania, United Republic of", "Togo", "Uganda", "Zambia", "Zimbabwe",
];

const List<String> kProducts = [
  "Bambara groundnut", "Banana", "Beans (mixed)", "Cassava", "Chili Pepper",
  "Coffee", "Cotton", "Cowpea", "Groundnuts (In Shell)", "Maize", "Millet",
  "Okras", "Onions", "Other", "Pigeon Pea", "Potato", "Rice", "Sesame Seed",
  "Sorghum", "Soybean", "Sunflower Seed", "Sweet Potatoes", "Taro", "Tomato",
  "Wheat", "Yams",
];

const List<String> kSeasons = ["Annual", "Dry", "Main", "Meher", "Other", "Summer", "Wet"];

const List<String> kProductionSystems = [
  "All (PS)", "Commercial (PS)", "Other", "Rainfed (PS)", "irrigated", "none",
];

void main() {
  runApp(const CropYieldApp());
}

class CropYieldApp extends StatelessWidget {
  const CropYieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    const gold = Color(0xFFC9A227);
    const dark = Color(0xFF121212);
    const surface = Color(0xFF1E1E1E);

    return MaterialApp(
      title: 'Crop Yield Predictor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: gold,
          brightness: Brightness.dark,
          primary: gold,
          surface: surface,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: dark,
          foregroundColor: gold,
          elevation: 0,
          centerTitle: true,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: surface,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: gold, width: 1.5),
          ),
          labelStyle: const TextStyle(color: Colors.white70),
          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: gold,
            foregroundColor: Colors.black,
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            textStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
        ),
      ),
      home: const PredictionPage(),
    );
  }
}

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;
  String? _resultText;
  bool _resultIsError = false;

  // Categorical (dropdown) selections -- 4 of the 9 model variables.
  String? _country = "Burundi";
  String? _product = "Maize";
  String? _season = "Main";
  String? _prodSystem = "Rainfed (PS)";

  // Numeric (text field) inputs -- the remaining 5 of the 9 model variables.
  final _plantingYearCtrl = TextEditingController(text: "2022");
  final _plantingMonthCtrl = TextEditingController(text: "9");
  final _harvestYearCtrl = TextEditingController(text: "2023");
  final _harvestMonthCtrl = TextEditingController(text: "2");
  final _areaCtrl = TextEditingController(text: "1500");

  @override
  void dispose() {
    _plantingYearCtrl.dispose();
    _plantingMonthCtrl.dispose();
    _harvestYearCtrl.dispose();
    _harvestMonthCtrl.dispose();
    _areaCtrl.dispose();
    super.dispose();
  }

  String? _requiredNumber(String? value, {double? min, double? max, bool isInt = false}) {
    if (value == null || value.trim().isEmpty) return "Required";
    final n = isInt ? int.tryParse(value.trim()) : double.tryParse(value.trim());
    if (n == null) return "Enter a number";
    if (min != null && n < min) return "Must be \u2265 $min";
    if (max != null && n > max) return "Must be \u2264 $max";
    return null;
  }

  Future<void> _predict() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) {
      setState(() {
        _resultText = "Please fix the highlighted fields.";
        _resultIsError = true;
      });
      return;
    }

    setState(() {
      _loading = true;
      _resultText = null;
      _resultIsError = false;
    });

    final body = {
      "country": _country,
      "product": _product,
      "season_name": _season,
      "crop_production_system": _prodSystem,
      "planting_year": int.parse(_plantingYearCtrl.text.trim()),
      "planting_month": int.parse(_plantingMonthCtrl.text.trim()),
      "harvest_year": int.parse(_harvestYearCtrl.text.trim()),
      "harvest_month": int.parse(_harvestMonthCtrl.text.trim()),
      "area": double.parse(_areaCtrl.text.trim()),
    };

    try {
      final response = await http
          .post(
            Uri.parse("$kApiBaseUrl/predict"),
            headers: {"Content-Type": "application/json"},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 20));

      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        final yieldVal = decoded["predicted_yield_t_per_ha"];
        setState(() {
          _resultText = "Predicted Yield: $yieldVal t/ha";
          _resultIsError = false;
        });
      } else {
        var message = response.body;
        try {
          final decoded = jsonDecode(response.body);
          if (decoded is Map<String, dynamic>) {
            message = decoded['detail']?.toString() ?? decoded['message']?.toString() ?? response.body;
          }
        } catch (_) {
          // Keep the raw body if the response is not valid JSON.
        }
        setState(() {
          _resultText = "Error (${response.statusCode}): $message";
          _resultIsError = true;
        });
      }
    } catch (e) {
      setState(() {
        _resultText = "Network error: could not reach the API. $e";
        _resultIsError = true;
      });
    } finally {
      setState(() => _loading = false);
    }
  }

  Widget _dropdown({
    required String label,
    required String? value,
    required List<String> items,
    required ValueChanged<String?> onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<String>(
        initialValue: value,
        isExpanded: true,
        dropdownColor: const Color(0xFF1E1E1E),
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(labelText: label),
        items: items
            .map((v) => DropdownMenuItem(value: v, child: Text(v, overflow: TextOverflow.ellipsis)))
            .toList(),
        onChanged: onChanged,
        validator: (v) => v == null ? "Required" : null,
      ),
    );
  }

  Widget _numberField({
    required TextEditingController controller,
    required String label,
    required String hint,
    double? min,
    double? max,
    bool isInt = true,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        style: const TextStyle(color: Colors.white),
        keyboardType: TextInputType.numberWithOptions(decimal: !isInt),
        inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*$'))],
        decoration: InputDecoration(labelText: label, hintText: hint, hintStyle: const TextStyle(color: Colors.white38)),
        validator: (v) => _requiredNumber(v, min: min, max: max, isInt: isInt),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Crop Yield Predictor")),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const Text(
                "Enter a crop observation to predict yield (t/ha)",
                style: TextStyle(color: Colors.white70, fontSize: 14),
              ),
              const SizedBox(height: 16),
              _dropdown(label: "Country", value: _country, items: kCountries, onChanged: (v) => setState(() => _country = v)),
              _dropdown(label: "Crop", value: _product, items: kProducts, onChanged: (v) => setState(() => _product = v)),
              _dropdown(label: "Season", value: _season, items: kSeasons, onChanged: (v) => setState(() => _season = v)),
              _dropdown(label: "Production System", value: _prodSystem, items: kProductionSystems, onChanged: (v) => setState(() => _prodSystem = v)),
              _numberField(controller: _plantingYearCtrl, label: "Planting Year", hint: "e.g. 2022", min: 1960, max: 2026),
              _numberField(controller: _plantingMonthCtrl, label: "Planting Month", hint: "1 - 12", min: 1, max: 12),
              _numberField(controller: _harvestYearCtrl, label: "Harvest Year", hint: "e.g. 2023", min: 1960, max: 2027),
              _numberField(controller: _harvestMonthCtrl, label: "Harvest Month", hint: "1 - 12", min: 1, max: 12),
              _numberField(controller: _areaCtrl, label: "Area (hectares)", hint: "e.g. 1500", min: 0, max: 379533.78, isInt: false),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _loading ? null : _predict,
                  child: _loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                        )
                      : const Text("Predict"),
                ),
              ),
              const SizedBox(height: 20),
              if (_resultText != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: _resultIsError ? Colors.red.withValues(alpha: 0.12) : const Color(0xFFC9A227).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: _resultIsError ? Colors.redAccent : const Color(0xFFC9A227)),
                  ),
                  child: Text(
                    _resultText!,
                    style: TextStyle(
                      color: _resultIsError ? Colors.redAccent : const Color(0xFFC9A227),
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
