import 'whatwg-fetch'; // fetch polyfill

import endpoints from './endpoints';

export function requestEntitlements(email, username, course_key) {
	console.log('called requestEntitlements api function');
  return fetch(
    `${endpoints.entitlementList}/?username_or_email=${email}`, {
      credentials: 'same-origin',
      method: 'get',
    },
  );
}

export function createEntitlement(email, username, course_key) {
  return fetch(
    `${endpoints.entitlementList}/?username_or_email=${email}`, {
      credentials: 'same-origin',
      method: 'post',
      body:{}
    },
  );
}

export function updateEntitlement(reason, entitlement_uuid, comments) {
  return fetch(
    `${endpoints.entitlementList}/?username_or_email=${email}`, {
      credentials: 'same-origin',
      method: 'put',
      body:{
      	reason: reason,
      	entitlement_uuid: entitlement_uuid,
      	comments: comments
      }
    },
  );
}