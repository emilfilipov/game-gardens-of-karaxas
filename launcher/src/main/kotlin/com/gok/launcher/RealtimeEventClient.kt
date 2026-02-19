package com.gok.launcher

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import java.net.URI
import java.net.http.HttpClient
import java.net.http.WebSocket
import java.time.Duration
import java.util.concurrent.CompletionStage
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

class RealtimeEventClient(
    private val uriProvider: () -> URI,
    private val onEvent: (JsonNode) -> Unit,
    private val onDisconnect: (String) -> Unit,
) {
    private val mapper = jacksonObjectMapper()
    private val httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build()
    private val scheduler = Executors.newSingleThreadScheduledExecutor { runnable ->
        Thread(runnable, "karaxas-events-ws").apply { isDaemon = true }
    }
    private val running = AtomicBoolean(false)
    @Volatile private var socket: WebSocket? = null
    @Volatile private var pingTask: ScheduledFuture<*>? = null

    fun start() {
        if (!running.compareAndSet(false, true)) return
        scheduleConnect(0)
    }

    fun stop() {
        if (!running.compareAndSet(true, false)) return
        try {
            pingTask?.cancel(false)
            pingTask = null
            socket?.sendClose(WebSocket.NORMAL_CLOSURE, "shutdown")
        } catch (_: Exception) {
            socket?.abort()
        } finally {
            socket = null
            scheduler.shutdownNow()
        }
    }

    fun sendJson(payload: Map<String, Any?>): Boolean {
        if (!running.get()) return false
        val encoded = try {
            mapper.writeValueAsString(payload)
        } catch (_: Exception) {
            return false
        }
        return try {
            socket?.sendText(encoded, true)
            socket != null
        } catch (_: Exception) {
            false
        }
    }

    private fun scheduleConnect(delaySeconds: Long) {
        if (!running.get()) return
        scheduler.schedule({ connectInternal() }, delaySeconds.coerceAtLeast(0), TimeUnit.SECONDS)
    }

    private fun connectInternal() {
        if (!running.get()) return
        val uri = try {
            uriProvider()
        } catch (ex: Exception) {
            onDisconnect("event_stream_uri_failed:${ex.javaClass.simpleName}")
            scheduleConnect(4)
            return
        }
        httpClient.newWebSocketBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .buildAsync(uri, Listener())
            .whenComplete { ws, err ->
                if (!running.get()) {
                    ws?.abort()
                    return@whenComplete
                }
                if (err != null || ws == null) {
                    onDisconnect("event_stream_connect_failed")
                    scheduleConnect(4)
                    return@whenComplete
                }
                socket = ws
                pingTask?.cancel(false)
                pingTask = scheduler.scheduleAtFixedRate(
                    {
                        try {
                            socket?.sendText("ping", true)
                        } catch (_: Exception) {
                            // listener close/error path will reconnect
                        }
                    },
                    12,
                    12,
                    TimeUnit.SECONDS
                )
            }
    }

    private inner class Listener : WebSocket.Listener {
        override fun onOpen(webSocket: WebSocket) {
            webSocket.request(1)
        }

        override fun onText(webSocket: WebSocket, data: CharSequence, last: Boolean): CompletionStage<*>? {
            if (last) {
                try {
                    val payload = mapper.readTree(data.toString())
                    onEvent(payload)
                } catch (_: Exception) {
                    // Ignore malformed events and continue stream.
                }
            }
            webSocket.request(1)
            return null
        }

        override fun onClose(webSocket: WebSocket, statusCode: Int, reason: String): CompletionStage<*>? {
            pingTask?.cancel(false)
            pingTask = null
            socket = null
            if (running.get()) {
                onDisconnect("event_stream_closed:$statusCode")
                scheduleConnect(3)
            }
            return null
        }

        override fun onError(webSocket: WebSocket, error: Throwable) {
            pingTask?.cancel(false)
            pingTask = null
            socket = null
            if (running.get()) {
                onDisconnect("event_stream_error:${error.javaClass.simpleName}")
                scheduleConnect(3)
            }
        }
    }
}
