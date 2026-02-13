import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AmountInput extends StatelessWidget {
  final TextEditingController controller;
  final String? labelText;

  const AmountInput({
    super.key,
    required this.controller,
    this.labelText,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      inputFormatters: [
        FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
      ],
      decoration: InputDecoration(
        labelText: labelText ?? 'Amount',
        prefixText: '\$ ',
      ),
      validator: (value) {
        if (value == null || value.isEmpty) return 'Amount is required';
        final amount = double.tryParse(value);
        if (amount == null || amount <= 0) return 'Enter a valid amount';
        return null;
      },
    );
  }
}
