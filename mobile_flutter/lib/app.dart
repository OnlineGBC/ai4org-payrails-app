import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'config/theme.dart';
import 'router/router.dart';

class PayRailsApp extends ConsumerWidget {
  const PayRailsApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.read(routerProvider);

    return MaterialApp.router(
      title: 'PayRails',
      theme: PayRailsTheme.lightTheme,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
