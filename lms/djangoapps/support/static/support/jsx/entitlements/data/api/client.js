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

export function createEntitlement(course_uuid, user, mode, reason, comments) {
  return fetch(
    `${endpoints.entitlementList}/?username_or_email=${email}`, {
      credentials: 'same-origin',
      method: 'post',
      body:{
        course_uuid: entitlement_uuid,
        user: user,
        mode: mode,
        reason: reason,
        comments: comments}
    },
  );
}

export function updateEntitlement(entitlement_uuid, reason, comments) {
  return fetch(
    `${endpoints.entitlementList}/?username_or_email=${email}`, {
      credentials: 'same-origin',
      method: 'put',
      body:{
      	entitlement_uuid: entitlement_uuid,
        reason: reason,
      	comments: comments
      }
    },
  );
}