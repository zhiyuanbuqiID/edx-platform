//increment
import entitlements from '../data/entitlements';
import * as clientApi from '../data/api/client';

export const entitlementActions = {
	FETCH_ENTITLEMENTS_REQUEST: 'FETCH_ENTITLEMENTS_REQUEST',
	FETCH_ENTITLEMENTS_SUCCESS: 'FETCH_ENTITLEMENTS_SUCCESS',
	FETCH_ENTITLEMENTS_FAILURE: 'FETCH_ENTITLEMENTS_FAILURE'

}

export function fetchEntitlements(email, username, course_key){
	console.log("fetchEntitlements action creation")
	return dispatch => {
		clientApi.requestEntitlements(email, username, course_key)
		.then((response) => {
      if (response.ok) {
        return response.json();
      }
      console.log('throwing error');
      throw new Error(response);
    })
    .then((json) => {
      if (json) {
      	console.log('got out some json', JSON.stringify(json))
        return dispatch(fetchEntitlementsSuccess(json.results));
      }
      return Promise.resolve();
    })
    .catch((error) => {
    	console.log('catching error');
      return dispatch(fetchEntitlementsFailure(error));  
    });
	}
}
export function fetchEntitlementsRequest(email, username, course_key){
	return {
		type:'FETCH_ENTITLEMENTS_REQUEST',
		email,
		username,
		course_key
	}
}

export function fetchEntitlementsSuccess(entitlements){
	return {
		type:'FETCH_ENTITLEMENTS_SUCCESS',
		entitlements
	}
}

export function fetchEntitlementsFailure(error){
	return {
		type:'FETCH_ENTITLEMENTS_FAILURE',
		error
	}
}

export function updateEntitlement(reason, entitlement_uuid, comments){
	console.log("fetchEntitlements action creation")
	return dispatch => {
		clientApi.updateEntitlement(reason, entitlement_uuid, comments)
		.then((response) => {
      if (response.ok) {
        return response.json();
      }
      console.log('throwing error');
      throw new Error(response);
    })
    .then((json) => {
      if (json) {
      	console.log('got out some json', JSON.stringify(json))
        return dispatch(updateEntitlementSuccess(json.results));
      }
      return Promise.resolve();
    })
    .catch((error) => {
    	console.log('catching error');
      return dispatch(updateEntitlementFailure(error));  
    });
	}
}
export function updateEntitlementRequest(reason, entitlement_uuid, comments){
	return {
		type:'UPDATE_ENTITLEMENT_REQUEST',
		email,
		username,
		course_key
	}
}

export function updateEntitlementSuccess(entitlement){
	return {
		type:'UPDATE_ENTITLEMENT_SUCCESS',
		entitlement
	}
}

export function updateEntitlementFailure(error){
	return {
		type:'UPDATE_ENTITLEMENT_FAILURE',
		error
	}
}

export function openEntitlementReissueModal(entitlement){
	return {
		type:'OPEN_REISSUE_MODAL',
		entitlement
	}
}

export function closeEntitlementReissueModal(){
	return {
		type:'CLOSE_REISSUE_MODAL',
		entitlement
	}
}

export function openEntitlementCreationModal(){
	return {
		type:'OPEN_CREATION_MODAL',
	}
}

export function closeEntitlementCreationModal(){
	return {
		type:'CLOSE_CREATION_MODAL',
	}
}


// updateEntitlement
