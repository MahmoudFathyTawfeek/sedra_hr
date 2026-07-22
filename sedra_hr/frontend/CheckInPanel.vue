<template>
	<div class="flex flex-col bg-white rounded-lg w-full py-5 px-4 border border-gray-100 shadow-sm">
		<div class="flex items-center gap-3">
			<div
				class="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm shrink-0"
				style="background-color: #0B2545"
			>
				{{ employee?.data?.first_name?.[0] }}
			</div>
			<div>
				<h2 class="text-base font-bold text-gray-900 leading-tight">
					{{ __("Hey, {0} 👋", [employee?.data?.first_name]) }}
				</h2>
				<div class="font-medium text-xs text-gray-500 mt-0.5" v-if="lastLog">
					<span>{{ __("Last {0} was at {1}", [__(lastLogType), formatTimestamp(lastLog.time)]) }}</span>
					<span class="whitespace-pre"> &middot; </span>
					<router-link :to="{ name: 'EmployeeCheckinListView' }" v-slot="{ navigate }">
						<span @click="navigate" class="underline" style="color: #0B2545">View List</span>
					</router-link>
				</div>
				<div v-else class="font-medium text-xs text-gray-500 mt-0.5">
					{{ dayjs().format("ddd, D MMMM, YYYY") }}
				</div>
			</div>
		</div>

		<template v-if="settings.data?.allow_employee_checkin_from_mobile_app">
			<Button
				class="mt-4 py-5 text-base text-white border-none"
				style="background-color: #0B2545"
				id="open-checkin-modal"
				@click="handleEmployeeCheckin"
			>
				<template #prefix>
					<FeatherIcon
						:name="nextAction.action === 'IN' ? 'arrow-right-circle' : 'arrow-left-circle'"
						class="w-4"
					/>
				</template>
				{{ nextAction.label }}
			</Button>
		</template>
	</div>

	<ion-modal
		v-if="settings.data?.allow_employee_checkin_from_mobile_app"
		ref="modal"
		trigger="open-checkin-modal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<div class="w-full flex flex-col items-center gap-5 p-5 pb-6 relative">
    <button
        class="absolute top-0 right-2 w-8 h-8 rounded-full flex items-center justify-center bg-gray-100 text-gray-600"
        @click="cancelCheckin"
    >
        <FeatherIcon name="x" class="w-4" />
    </button>
			<div class="w-full rounded-lg py-3 px-4 flex flex-col items-center" style="background-color: #0B2545">
				<div class="font-bold text-2xl text-white tracking-wide">
					{{ dayjs(checkinTimestamp).format("hh:mm:ss a") }}
				</div>
				<div class="font-medium text-gray-300 text-xs mt-0.5">
					{{ dayjs().format("D MMM, YYYY") }}
				</div>
			</div>

			<template v-if="settings.data?.allow_geolocation_tracking">
				<span v-if="locationStatus" class="font-medium text-gray-500 text-xs -mb-2">
					{{ locationStatus }}
				</span>
				<div class="rounded-lg border translate-z-0 block overflow-hidden w-full" style="border-color: #0B2545">
					<iframe
						width="100%"
						height="150"
						frameborder="0"
						scrolling="no"
						marginheight="0"
						marginwidth="0"
						style="border: 0"
						:src="`https://maps.google.com/maps?q=${latitude},${longitude}&hl=en&z=15&amp;output=embed`"
					>
					</iframe>
				</div>
			</template>

			<!-- ======= PHOTO STEP ======= -->
			<div class="w-full flex flex-col items-center gap-3">
				<div v-if="photoStep === 'capture'" class="w-full flex flex-col items-center gap-3">
					<div
						class="relative w-48 h-48 rounded-full overflow-hidden border-4 flex items-center justify-center bg-gray-900"
						style="border-color: #0B2545"
					>
						<video
							ref="videoEl"
							autoplay
							playsinline
							muted
							class="w-full h-full object-cover"
						></video>
					</div>
					<p class="text-gray-500 text-xs text-center">{{ __("Center your face in the frame") }}</p>
					<p v-if="cameraError" class="text-red-500 text-sm text-center">{{ cameraError }}</p>
					<Button
						variant="solid"
						class="w-full py-5 text-sm text-white border-none"
						style="background-color: #0B2545"
						@click="capturePhoto"
					>
						<template #prefix><FeatherIcon name="camera" class="w-4" /></template>
						{{ __("Take Photo") }}
					</Button>
				</div>

				<div v-else-if="photoStep === 'preview'" class="w-full flex flex-col items-center gap-3">
					<div class="relative w-48 h-48 rounded-full overflow-hidden border-4" style="border-color: #0B2545">
						<img :src="photoDataUrl" class="w-full h-full object-cover" />
						<div
							class="absolute bottom-1 right-1 w-7 h-7 rounded-full flex items-center justify-center text-white"
							style="background-color: #16a34a"
						>
							<FeatherIcon name="check" class="w-4" />
						</div>
					</div>
					<div class="flex gap-2 w-full">
						<Button
							variant="outline"
							class="flex-1 py-5 text-sm"
							style="border-color: #0B2545; color: #0B2545"
							@click="retakePhoto"
						>
							<template #prefix><FeatherIcon name="refresh-cw" class="w-4" /></template>
							{{ __("Retake") }}
						</Button>
						<Button
							:loading="checkins.insert.loading"
							variant="solid"
							class="flex-1 py-5 text-sm text-white border-none"
							style="background-color: #0B2545"
							@click="submitLog(nextAction.action)"
						>
							{{ __("Confirm {0}", [nextAction.label]) }}
						</Button>
					</div>
				</div>
			</div>
			<!-- ======= END PHOTO STEP ======= -->
		</div>
	</ion-modal>
</template>

<script setup>
import { createListResource, toast, FeatherIcon } from "frappe-ui"
import { computed, inject, ref, onMounted, onBeforeUnmount, nextTick } from "vue"
import { IonModal, modalController } from "@ionic/vue"

import { formatTimestamp } from "@/utils/formatters"
import { settings } from "@/data/settings"

const DOCTYPE = "Employee Checkin"

const socket = inject("$socket")
const employee = inject("$employee")
const dayjs = inject("$dayjs")
const __ = inject("$translate")
const checkinTimestamp = ref(null)
const latitude = ref(0)
const longitude = ref(0)
const locationStatus = ref("")

// ---- Photo state ----
const photoStep = ref("capture")
const photoDataUrl = ref(null)
const cameraError = ref("")
const videoEl = ref(null)
let stream = null

const checkins = createListResource({
	doctype: DOCTYPE,
	fields: ["name", "employee", "employee_name", "log_type", "time", "device_id"],
	filters: { employee: employee.data.name },
	orderBy: "time desc",
})
checkins.reload()

const lastLog = computed(() => {
	if (checkins.list.loading || !checkins.data) return {}
	return checkins.data[0]
})

const lastLogType = computed(() => {
	return lastLog?.value?.log_type === "IN" ? "check-in" : "check-out"
})

const nextAction = computed(() => {
	return lastLog?.value?.log_type === "IN"
		? { action: "OUT", label: __("Check Out") }
		: { action: "IN", label: __("Check In") }
})

function handleLocationSuccess(position) {
	latitude.value = position.coords.latitude
	longitude.value = position.coords.longitude
	locationStatus.value = [
		__("Latitude: {0}°", [Number(latitude.value).toFixed(5)]),
		__("Longitude: {0}°", [Number(longitude.value).toFixed(5)]),
	].join(", ")
}

function handleLocationError(error) {
	locationStatus.value = "Unable to retrieve your location"
	if (error) locationStatus.value += `: ERROR(${error.code}): ${error.message}`
}

const fetchLocation = () => {
	if (!navigator.geolocation) {
		locationStatus.value = __("Geolocation is not supported by your current browser")
	} else {
		locationStatus.value = __("Locating...")
		navigator.geolocation.getCurrentPosition(handleLocationSuccess, handleLocationError)
	}
}

async function startCamera() {
	cameraError.value = ""
	photoStep.value = "capture"
	photoDataUrl.value = null

	if (!navigator.mediaDevices?.getUserMedia) {
		cameraError.value = __("Camera is not supported on this device or browser.")
		return
	}

	try {
		stream = await navigator.mediaDevices.getUserMedia({
			video: { facingMode: "user" },
			audio: false,
		})
		await nextTick()
		if (videoEl.value) {
			videoEl.value.srcObject = stream
		}
	} catch (err) {
		if (err.name === "NotAllowedError") {
			cameraError.value = __("Camera permission denied. Please allow camera access and try again.")
		} else if (err.name === "NotFoundError") {
			cameraError.value = __("No camera found on this device.")
		} else {
			cameraError.value = __("Camera error: {0}", [err.message])
		}
	}
}

function stopCamera() {
	if (stream) {
		stream.getTracks().forEach((t) => t.stop())
		stream = null
	}
}

function cancelCheckin() {
    stopCamera()
    photoStep.value = "capture"
    photoDataUrl.value = null
    modalController.dismiss()
}

function capturePhoto() {
	if (!videoEl.value) return

	const canvas = document.createElement("canvas")
	canvas.width = videoEl.value.videoWidth
	canvas.height = videoEl.value.videoHeight
	canvas.getContext("2d").drawImage(videoEl.value, 0, 0)

	let quality = 0.85
	let dataUrl = canvas.toDataURL("image/jpeg", quality)
	while (dataUrl.length > 1_000_000 && quality > 0.3) {
		quality -= 0.1
		dataUrl = canvas.toDataURL("image/jpeg", quality)
	}

	photoDataUrl.value = dataUrl
	photoStep.value = "preview"
	stopCamera()
}

function retakePhoto() {
	photoDataUrl.value = null
	startCamera()
}

const handleEmployeeCheckin = () => {
	checkinTimestamp.value = dayjs().format("YYYY-MM-DD HH:mm:ss")
	if (settings.data?.allow_geolocation_tracking) fetchLocation()
	setTimeout(startCamera, 400)
}

async function dataUrlToFile(dataUrl, filename) {
	const res = await fetch(dataUrl)
	const blob = await res.blob()
	return new File([blob], filename, { type: "image/jpeg" })
}

const submitLog = async (logType) => {
	if (!photoDataUrl.value) {
		toast({
			title: __("Photo Required"),
			text: __("Please take a selfie before checking in."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	const actionLabel = logType === "IN" ? __("Check-in") : __("Check-out")

	let photoUrl = null
	try {
		const file = await dataUrlToFile(
			photoDataUrl.value,
			`checkin_${employee.data.name}_${Date.now()}.jpg`
		)
		const formData = new FormData()
		formData.append("file", file)
		formData.append("is_private", "1")
		formData.append("doctype", DOCTYPE)

		const uploadRes = await fetch("/api/method/frappe.handler.upload_file", {
			method: "POST",
			headers: {
				"X-Frappe-CSRF-Token": frappe.csrf_token,
				"X-Requested-With": "XMLHttpRequest",
			},
			body: formData,
		})

		const uploadData = await uploadRes.json()
		photoUrl = uploadData.message?.file_url
		if (!photoUrl) throw new Error("No file_url in response")

	} catch (err) {
		toast({
			title: __("Upload Failed"),
			text: err.message,
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	checkins.insert.submit(
		{
			employee: employee.data.name,
			log_type: logType,
			time: checkinTimestamp.value,
			latitude: latitude.value,
			longitude: longitude.value,
			custom_employee_photo: photoUrl,
		},
		{
			onSuccess() {
				stopCamera()
				modalController.dismiss()
				toast({
					title: __("Success"),
					text: __("{0} successful!", [actionLabel]),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				let messages = error.messages || []
				for (const message of messages) {
					toast({
						title: __("Error"),
						text: message || __("{0} failed!", [actionLabel]),
						icon: "alert-circle",
						position: "bottom-center",
						iconClasses: "text-red-500",
					})
				}
			},
		}
	)
}

onMounted(() => {
	socket.emit("doctype_subscribe", DOCTYPE)
	socket.on("list_update", (data) => {
		if (data.doctype == DOCTYPE) checkins.reload()
	})
})

onBeforeUnmount(() => {
	stopCamera()
	socket.emit("doctype_unsubscribe", DOCTYPE)
	socket.off("list_update")
})
</script>