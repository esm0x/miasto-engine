package com.adminstack.rybnik.widget

/**
 * The widget under the class name the single-city Rybnik app registered it with.
 *
 * A home-screen widget is bound to its receiver's component name. Moving Rybnik onto
 * the engine renamed the package, and without this every widget people had placed
 * would turn into "Nie można załadować widżetu" on the update. The rybnik flavour's
 * manifest declares this class instead of the engine's one, so it is the same widget
 * under the old name.
 */
class WasteWidgetReceiver : com.adminstack.miasto.widget.WasteWidgetReceiver()
