'use strict';

angular
    .module('loom.controllers')
    .controller('FileDetailController', FileDetailController);

FileDetailController.$inject = [
    '$scope', '$http', 'Data', '$stateParams'
];

function FileDetailController($scope, $http, Data, $stateParams) {
    $http.get('/api/file_data_objects/'+ $stateParams.fileId)
	.success(function(response) {
	    Data.file = response;
	    $http.get('/api/file_data_objects/' + $stateParams.fileId + '/data_source_records/')
		.then(function(response){
		    Data.file['data_source_records'] = response['data']['data_source_records'];
		});
	    $http.get('/api/file_data_objects/' + $stateParams.fileId + '/file_storage_locations/')
		.then(function(response){
		    Data.file['file_storage_locations'] = response['data']['file_storage_locations'];
		});
	    $scope.file = Data.file;
	});
};
