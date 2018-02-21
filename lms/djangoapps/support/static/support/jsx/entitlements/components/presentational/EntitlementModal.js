import React from 'react';
import { Modal, Button } from '@edx/paragon';

class EntitlementModalForm extends React.Component{
	constructor(props){
		super(props)
	}
	render(){
		return (
	    <form ref="entitlementModalForm" className="search-form" onSubmit={this.handleSubmit.bind(this)}>
				mode', 'course_uuid', 'username_or_email', and 'reason'
				<input type="text" ref="user" placeholder="user"/>
				<input type="text" ref="courseUuid" placeholder="user name"/>
				<input type="text" ref="mode" placeholder="mode"/>
				<input type="text" ref="reason" placeholder="reason"/>
			</form>
	   )
	}
}

class EntitlementModal extends React.Component{
	constructor(props){
		super(props)
	}

	submitForm(){
		console.log('submitForm')
	}
	onClose(){
		console.log('close model')
	}
	render(){
		const title = this.props.activeEntitlement ? "Re-issue Entitlement" : "Create Entitlement"
		
		return (
			<div/>
      	<Modal  open={this.props.modalOpen} title={title}
	      body="This is a form"
	      buttons={[
	      	<Button
	          label="submit"
	          buttonType="light"
	          onClick = {this.submitForm.bind(this)}/>]},
	      onClose = {this.onClose()}
    		/>
   )
	}
}

export default EntitlementModal;
