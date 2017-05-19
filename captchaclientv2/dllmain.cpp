/* Replace "dll.h" with the name of your header */
#include "stdafx.h"

#include "captchaclientv2.h"
#include <windows.h>
#pragma unmanaged

BOOL WINAPI DllMain(HINSTANCE hinstDLL,DWORD fdwReason,LPVOID lpvReserved)
{
	switch(fdwReason)
	{
		case DLL_PROCESS_ATTACH:
		{
			curl_global_init(CURL_GLOBAL_ALL);
			//printf("DLL_PROCESS_ATTACH");
			break;
		}
		case DLL_PROCESS_DETACH:
		{
			curl_global_cleanup();
			break;
		}
		case DLL_THREAD_ATTACH:
		{
			//printf("DLL_THREAD_ATTACH");
			break;
		}
		case DLL_THREAD_DETACH:
		{
			break;
		}
	}
	
	/* Return TRUE on success, FALSE on failure */
	return TRUE;
}
