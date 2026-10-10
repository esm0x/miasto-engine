package com.adminstack.miasto.data.waste

import com.adminstack.miasto.core.city.City
import android.content.Context
import com.adminstack.miasto.core.net.CachedRemoteSource
import com.adminstack.miasto.core.net.RemoteConfig
import com.adminstack.miasto.core.net.sharedJson

class WasteRepository(context: Context) :
    CachedRemoteSource<WastePayload>(context, RemoteConfig.dataUrl("waste.json"), "waste.json") {

    override val enabled: Boolean get() = City.config.modules.waste

    override fun parse(body: String): WastePayload = sharedJson.decodeFromString(body)

    fun schedule(): WasteSchedule = WasteSchedule(data.value?.rejony ?: emptyList())
}
